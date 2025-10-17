#!/usr/bin/env python3
"""
ローカルダッシュボードサーバー（改良版）
期間フィルター機能と元データ表示機能付き
"""

import os
import json
import logging
from flask import Flask, render_template_string, jsonify, request
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import webbrowser
import threading
import time

# 環境変数を読み込み
load_dotenv()

# Flaskアプリ初期化
app = Flask(__name__)

# 設定
DATA_DIR = Path(os.getenv('DATA_DIR', './data'))
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 8081))
AUTO_OPEN_BROWSER = os.getenv('AUTO_OPEN_BROWSER', 'true').lower() == 'true'

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ダッシュボードHTMLテンプレート（拡張版）
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>美容・健康成分トレンド分析ダッシュボード (改良版)</title>

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>

    <style>
        .card { transition: transform 0.2s; }
        .card:hover { transform: translateY(-4px); }
        .gradient-bg {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .loading {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: .5; }
        }
        .tab-active {
            border-bottom: 3px solid #667eea;
            color: #667eea;
        }
        .raw-data {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-bottom: 1rem;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            word-break: break-all;
        }
    </style>
</head>
<body class="bg-gray-50">
    <!-- ヘッダー -->
    <header class="gradient-bg text-white p-6 shadow-lg">
        <div class="container mx-auto">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold">🧬 美容・健康成分トレンド分析</h1>
                    <p class="mt-2 text-purple-100">改良版ダッシュボード - 期間フィルター & 元データ表示対応</p>
                </div>
                <button onclick="refreshData()" class="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-lg transition">
                    🔄 データ更新
                </button>
            </div>
            <div class="mt-4 flex items-center space-x-4 text-sm">
                <span id="lastUpdate" class="bg-white/20 px-3 py-1 rounded-full loading">
                    最終更新: 読み込み中...
                </span>
                <span id="totalPapers" class="bg-white/20 px-3 py-1 rounded-full">
                    総論文数: 0件
                </span>
                <span class="bg-green-500/30 px-3 py-1 rounded-full">
                    🟢 ローカル実行中
                </span>
            </div>
        </div>
    </header>

    <!-- フィルターコントロール -->
    <div class="container mx-auto p-6">
        <div class="bg-white rounded-lg shadow-md p-4 mb-6">
            <div class="flex flex-wrap items-center gap-4">
                <div class="flex items-center gap-2">
                    <label class="font-semibold">期間フィルター:</label>
                    <select id="periodFilter" onchange="applyFilter()" class="border rounded px-3 py-1">
                        <option value="all">すべて</option>
                        <option value="7">過去7日間</option>
                        <option value="14">過去14日間</option>
                        <option value="30">過去30日間</option>
                        <option value="60">過去60日間</option>
                        <option value="90">過去90日間</option>
                        <option value="180">過去6ヶ月間</option>
                        <option value="365">過去1年間</option>
                        <option value="730">過去2年間</option>
                        <option value="1095">過去3年間</option>
                        <option value="1460">過去4年間</option>
                        <option value="1825">過去5年間</option>
                    </select>
                </div>
                <div class="flex items-center gap-2">
                    <label class="font-semibold">キーワード:</label>
                    <select id="keywordFilter" onchange="applyFilter()" class="border rounded px-3 py-1">
                        <option value="all">すべて</option>
                    </select>
                </div>
                <div class="flex items-center gap-2">
                    <label class="font-semibold">データ表示:</label>
                    <div class="flex gap-2">
                        <button onclick="switchView('summary')" id="summaryBtn" class="px-3 py-1 border rounded hover:bg-purple-100 tab-active">要約</button>
                        <button onclick="switchView('raw')" id="rawBtn" class="px-3 py-1 border rounded hover:bg-purple-100">元データ</button>
                        <button onclick="switchView('stats')" id="statsBtn" class="px-3 py-1 border rounded hover:bg-purple-100">統計</button>
                    </div>
                </div>
            </div>
            <div class="mt-2 text-sm text-gray-600">
                <span id="filterInfo">フィルター適用中: なし</span>
            </div>
        </div>
    </div>

    <!-- メインコンテンツ -->
    <main class="container mx-auto p-6">
        <!-- エラーメッセージ -->
        <div id="errorMessage" class="hidden bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong>エラー:</strong> <span id="errorText"></span>
        </div>

        <!-- サマリービュー -->
        <div id="summaryView" class="view-content">
            <!-- サマリーカード -->
            <div class="grid md:grid-cols-4 gap-4 mb-8">
                <div class="card bg-white rounded-lg shadow-md p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">対象論文数</p>
                            <p class="text-3xl font-bold text-purple-600" id="filteredPapers">-</p>
                        </div>
                        <div class="text-3xl">📄</div>
                    </div>
                </div>

                <div class="card bg-white rounded-lg shadow-md p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">注目成分</p>
                            <p class="text-xl font-bold text-pink-600" id="topIngredient">-</p>
                        </div>
                        <div class="text-3xl">🔬</div>
                    </div>
                </div>

                <div class="card bg-white rounded-lg shadow-md p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">平均重要度</p>
                            <p class="text-3xl font-bold text-green-600" id="avgImportance">-</p>
                        </div>
                        <div class="text-3xl">⭐</div>
                    </div>
                </div>

                <div class="card bg-white rounded-lg shadow-md p-6">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-gray-600 text-sm">分析キーワード</p>
                            <p class="text-3xl font-bold text-blue-600" id="keywordCount">-</p>
                        </div>
                        <div class="text-3xl">🏷️</div>
                    </div>
                </div>
            </div>

            <!-- グラフセクション -->
            <div class="grid md:grid-cols-2 gap-6 mb-8">
                <!-- キーワード別論文数 -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-bold mb-4 text-gray-800">📊 キーワード別論文数</h2>
                    <canvas id="keywordChart"></canvas>
                </div>

                <!-- 成分出現頻度 -->
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-bold mb-4 text-gray-800">🧪 注目成分TOP10</h2>
                    <canvas id="ingredientChart"></canvas>
                </div>
            </div>

            <!-- 論文リスト -->
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-bold mb-4 text-gray-800">📝 最新論文</h2>
                <div id="papersList" class="space-y-4">
                    <div class="loading text-center py-8">データを読み込み中...</div>
                </div>
            </div>
        </div>

        <!-- 元データビュー -->
        <div id="rawView" class="view-content hidden">
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-bold mb-4 text-gray-800">📊 生データ表示</h2>
                <div class="mb-4">
                    <button onclick="downloadRawData()" class="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">
                        💾 JSONファイルをダウンロード
                    </button>
                </div>
                <div id="rawDataContent" class="space-y-4">
                    <div class="loading text-center py-8">データを読み込み中...</div>
                </div>
            </div>
        </div>

        <!-- 統計ビュー -->
        <div id="statsView" class="view-content hidden">
            <div class="bg-white rounded-lg shadow-md p-6">
                <h2 class="text-xl font-bold mb-4 text-gray-800">📈 統計分析</h2>
                <div class="grid md:grid-cols-2 gap-6">
                    <!-- 時系列グラフ -->
                    <div>
                        <h3 class="text-lg font-semibold mb-2">論文数の推移</h3>
                        <canvas id="timelineChart"></canvas>
                    </div>
                    <!-- 重要度分布 -->
                    <div>
                        <h3 class="text-lg font-semibold mb-2">重要度スコア分布</h3>
                        <canvas id="importanceChart"></canvas>
                    </div>
                </div>
                <div class="mt-6">
                    <h3 class="text-lg font-semibold mb-2">詳細統計</h3>
                    <div id="statsDetails" class="grid md:grid-cols-3 gap-4">
                        <div class="loading text-center py-8 col-span-3">データを読み込み中...</div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <script>
        // グローバル変数
        let allData = null;
        let filteredData = null;
        let keywordChart = null;
        let ingredientChart = null;
        let timelineChart = null;
        let importanceChart = null;
        let currentView = 'summary';

        // ビュー切り替え
        function switchView(view) {
            currentView = view;
            document.querySelectorAll('.view-content').forEach(el => el.classList.add('hidden'));
            document.getElementById(view + 'View').classList.remove('hidden');

            // タブのアクティブ状態を更新
            document.querySelectorAll('[id$="Btn"]').forEach(btn => btn.classList.remove('tab-active'));
            document.getElementById(view + 'Btn').classList.add('tab-active');

            if (view === 'raw') {
                displayRawData();
            } else if (view === 'stats') {
                displayStats();
            }
        }

        // フィルター適用
        function applyFilter() {
            const period = document.getElementById('periodFilter').value;
            const keyword = document.getElementById('keywordFilter').value;

            if (!allData) return;

            // フィルタリング処理
            filteredData = filterData(allData, period, keyword);

            // フィルター情報更新
            updateFilterInfo(period, keyword);

            // 表示更新
            updateDisplay();
        }

        // データフィルタリング
        function filterData(data, period, keyword) {
            let result = JSON.parse(JSON.stringify(data)); // ディープコピー

            // 期間フィルター
            if (period !== 'all') {
                const cutoffDate = new Date();
                cutoffDate.setDate(cutoffDate.getDate() - parseInt(period));

                if (result.papers) {
                    Object.keys(result.papers).forEach(key => {
                        result.papers[key] = result.papers[key].filter(paper => {
                            const paperDate = new Date(paper.publication_date);
                            return paperDate >= cutoffDate;
                        });
                    });
                }
            }

            // キーワードフィルター
            if (keyword !== 'all' && result.papers) {
                const filtered = {};
                filtered[keyword] = result.papers[keyword] || [];
                result.papers = filtered;
            }

            return result;
        }

        // フィルター情報更新
        function updateFilterInfo(period, keyword) {
            let info = 'フィルター適用中: ';
            const filters = [];

            if (period !== 'all') {
                filters.push(`過去${period}日間`);
            }
            if (keyword !== 'all') {
                filters.push(`キーワード: ${keyword}`);
            }

            info += filters.length > 0 ? filters.join(', ') : 'なし';
            document.getElementById('filterInfo').textContent = info;
        }

        // データ読み込み
        async function loadData() {
            try {
                const response = await fetch('/api/data/full');
                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                allData = data;
                filteredData = data;

                // キーワードフィルターのオプションを更新
                updateKeywordOptions();

                // 表示更新
                updateDisplay();

                // エラーメッセージを隠す
                document.getElementById('errorMessage').classList.add('hidden');

            } catch (error) {
                document.getElementById('errorText').textContent = error.message;
                document.getElementById('errorMessage').classList.remove('hidden');
                console.error('データ読み込みエラー:', error);
            }
        }

        // キーワードオプション更新
        function updateKeywordOptions() {
            const select = document.getElementById('keywordFilter');
            select.innerHTML = '<option value="all">すべて</option>';

            if (allData && allData.papers) {
                Object.keys(allData.papers).forEach(keyword => {
                    const option = document.createElement('option');
                    option.value = keyword;
                    option.textContent = keyword;
                    select.appendChild(option);
                });
            }
        }

        // 表示更新
        function updateDisplay() {
            const data = filteredData || allData;

            if (!data) return;

            // サマリー更新
            updateSummary(data);

            // グラフ更新
            updateCharts(data);

            // 論文リスト更新
            updatePapersList(data.papers);

            // 最終更新時刻
            document.getElementById('lastUpdate').textContent =
                `最終更新: ${new Date(data.timestamp).toLocaleString('ja-JP')}`;
        }

        // サマリー更新
        function updateSummary(data) {
            let totalPapers = 0;
            let totalImportance = 0;
            let importanceCount = 0;

            if (data.papers) {
                Object.values(data.papers).forEach(papers => {
                    totalPapers += papers.length;
                    papers.forEach(paper => {
                        if (paper.ai_summary?.importance_score) {
                            totalImportance += paper.ai_summary.importance_score;
                            importanceCount++;
                        }
                    });
                });
            }

            document.getElementById('totalPapers').textContent = `総論文数: ${totalPapers}件`;
            document.getElementById('filteredPapers').textContent = totalPapers;
            document.getElementById('keywordCount').textContent = Object.keys(data.papers || {}).length;

            const avgImportance = importanceCount > 0 ? (totalImportance / importanceCount).toFixed(1) : '-';
            document.getElementById('avgImportance').textContent = avgImportance;

            // 注目成分を取得
            if (data.analysis?.ingredient_frequency && data.analysis.ingredient_frequency.length > 0) {
                document.getElementById('topIngredient').textContent =
                    data.analysis.ingredient_frequency[0].name;
            } else {
                document.getElementById('topIngredient').textContent = '-';
            }
        }

        // グラフ更新
        function updateCharts(data) {
            // キーワード別論文数
            if (data.papers) {
                const labels = Object.keys(data.papers);
                const values = labels.map(key => data.papers[key].length);

                updateKeywordChart(labels, values);
            }

            // 成分出現頻度
            if (data.analysis?.ingredient_frequency) {
                const ingredients = data.analysis.ingredient_frequency.slice(0, 10);
                updateIngredientChart(
                    ingredients.map(i => i.name),
                    ingredients.map(i => i.count)
                );
            }
        }

        // キーワードグラフ更新
        function updateKeywordChart(labels, data) {
            const ctx = document.getElementById('keywordChart').getContext('2d');

            if (keywordChart) {
                keywordChart.destroy();
            }

            keywordChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '論文数',
                        data: data,
                        backgroundColor: 'rgba(102, 126, 234, 0.5)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });
        }

        // 成分グラフ更新
        function updateIngredientChart(labels, data) {
            const ctx = document.getElementById('ingredientChart').getContext('2d');

            if (ingredientChart) {
                ingredientChart.destroy();
            }

            ingredientChart = new Chart(ctx, {
                type: 'horizontalBar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '出現回数',
                        data: data,
                        backgroundColor: 'rgba(236, 72, 153, 0.5)',
                        borderColor: 'rgba(236, 72, 153, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });
        }

        // 論文リスト更新
        function updatePapersList(papers) {
            const container = document.getElementById('papersList');

            if (!papers || Object.keys(papers).length === 0) {
                container.innerHTML = '<p class="text-gray-500">論文データがありません</p>';
                return;
            }

            container.innerHTML = Object.entries(papers)
                .map(([keyword, paperList]) => paperList.map(paper => `
                <div class="border rounded-lg p-4 hover:shadow-md transition">
                    <div class="flex justify-between items-start mb-2">
                        <h3 class="font-semibold text-lg flex-1">${paper.title}</h3>
                        <span class="text-xs bg-purple-100 text-purple-800 px-2 py-1 rounded ml-2">
                            ${keyword}
                        </span>
                    </div>
                    <p class="text-gray-600 text-sm mb-2">
                        ${paper.authors?.slice(0, 3).join(', ') || '著者情報なし'}
                        ${paper.authors?.length > 3 ? ' 他' : ''}
                    </p>
                    <div class="flex flex-wrap gap-2 mb-2">
                        ${(paper.ai_summary?.key_findings || []).map(finding =>
                            `<span class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                ${finding}
                            </span>`
                        ).join('')}
                    </div>
                    <div class="flex items-center space-x-4 text-xs text-gray-500">
                        <span>📅 ${paper.publication_date || '不明'}</span>
                        <span>⭐ ${paper.ai_summary?.importance_score || 0}/10</span>
                        <span>PMID: ${paper.pmid || 'N/A'}</span>
                        <a href="${paper.url}" target="_blank"
                           class="text-purple-600 hover:underline">
                            PubMedで見る →
                        </a>
                    </div>
                </div>
            `).join('')).flat().join('');
        }

        // 生データ表示
        function displayRawData() {
            const container = document.getElementById('rawDataContent');
            const data = filteredData || allData;

            if (!data) {
                container.innerHTML = '<p class="text-gray-500">データがありません</p>';
                return;
            }

            // 各論文の生データを表示
            if (data.papers) {
                const rawHtml = Object.entries(data.papers).map(([keyword, papers]) => `
                    <div class="mb-6">
                        <h3 class="font-bold text-lg mb-2">キーワード: ${keyword}</h3>
                        ${papers.map((paper, idx) => `
                            <div class="raw-data">
                                <div class="font-semibold mb-1">論文 ${idx + 1}:</div>
                                <pre>${JSON.stringify(paper, null, 2)}</pre>
                            </div>
                        `).join('')}
                    </div>
                `).join('');

                container.innerHTML = rawHtml;
            }
        }

        // 統計表示
        function displayStats() {
            const data = filteredData || allData;

            if (!data) return;

            // 時系列データ作成
            const timelineData = createTimelineData(data.papers);
            updateTimelineChart(timelineData);

            // 重要度分布作成
            const importanceData = createImportanceDistribution(data.papers);
            updateImportanceChart(importanceData);

            // 詳細統計表示
            displayDetailedStats(data);
        }

        // 時系列データ作成
        function createTimelineData(papers) {
            const timeline = {};

            if (papers) {
                Object.values(papers).flat().forEach(paper => {
                    if (paper.publication_date) {
                        const date = paper.publication_date.substring(0, 7); // YYYY-MM形式
                        timeline[date] = (timeline[date] || 0) + 1;
                    }
                });
            }

            const sorted = Object.entries(timeline).sort((a, b) => a[0].localeCompare(b[0]));
            return {
                labels: sorted.map(([date]) => date),
                values: sorted.map(([, count]) => count)
            };
        }

        // 重要度分布作成
        function createImportanceDistribution(papers) {
            const distribution = Array(11).fill(0); // 0-10のスコア

            if (papers) {
                Object.values(papers).flat().forEach(paper => {
                    const score = paper.ai_summary?.importance_score;
                    if (score !== undefined && score !== null) {
                        distribution[Math.round(score)]++;
                    }
                });
            }

            return distribution;
        }

        // 時系列グラフ更新
        function updateTimelineChart(data) {
            const ctx = document.getElementById('timelineChart').getContext('2d');

            if (timelineChart) {
                timelineChart.destroy();
            }

            timelineChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: '論文数',
                        data: data.values,
                        borderColor: 'rgba(59, 130, 246, 1)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });
        }

        // 重要度分布グラフ更新
        function updateImportanceChart(data) {
            const ctx = document.getElementById('importanceChart').getContext('2d');

            if (importanceChart) {
                importanceChart.destroy();
            }

            importanceChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'],
                    datasets: [{
                        label: '論文数',
                        data: data,
                        backgroundColor: 'rgba(16, 185, 129, 0.5)',
                        borderColor: 'rgba(16, 185, 129, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: { stepSize: 1 }
                        }
                    }
                }
            });
        }

        // 詳細統計表示
        function displayDetailedStats(data) {
            const container = document.getElementById('statsDetails');

            if (!data.papers) {
                container.innerHTML = '<p class="text-gray-500">統計データがありません</p>';
                return;
            }

            // 統計計算
            const allPapers = Object.values(data.papers).flat();
            const scores = allPapers
                .map(p => p.ai_summary?.importance_score)
                .filter(s => s !== undefined && s !== null);

            const stats = {
                total: allPapers.length,
                withSummary: allPapers.filter(p => p.ai_summary).length,
                avgScore: scores.length > 0 ? (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2) : 'N/A',
                maxScore: scores.length > 0 ? Math.max(...scores) : 'N/A',
                minScore: scores.length > 0 ? Math.min(...scores) : 'N/A',
                keywords: Object.keys(data.papers).length,
                dateRange: calculateDateRange(allPapers)
            };

            container.innerHTML = `
                <div class="bg-gray-50 p-4 rounded">
                    <div class="text-sm space-y-1">
                        <p><span class="font-semibold">総論文数:</span> ${stats.total}件</p>
                        <p><span class="font-semibold">要約済み:</span> ${stats.withSummary}件</p>
                        <p><span class="font-semibold">キーワード数:</span> ${stats.keywords}</p>
                    </div>
                </div>
                <div class="bg-gray-50 p-4 rounded">
                    <div class="text-sm space-y-1">
                        <p><span class="font-semibold">平均重要度:</span> ${stats.avgScore}</p>
                        <p><span class="font-semibold">最高スコア:</span> ${stats.maxScore}</p>
                        <p><span class="font-semibold">最低スコア:</span> ${stats.minScore}</p>
                    </div>
                </div>
                <div class="bg-gray-50 p-4 rounded">
                    <div class="text-sm space-y-1">
                        <p><span class="font-semibold">データ期間:</span></p>
                        <p class="text-xs">${stats.dateRange}</p>
                    </div>
                </div>
            `;
        }

        // 日付範囲計算
        function calculateDateRange(papers) {
            const dates = papers
                .map(p => p.publication_date)
                .filter(d => d)
                .sort();

            if (dates.length === 0) return '日付情報なし';

            return `${dates[0]} 〜 ${dates[dates.length - 1]}`;
        }

        // データダウンロード
        function downloadRawData() {
            const data = filteredData || allData;
            if (!data) {
                alert('ダウンロードするデータがありません');
                return;
            }

            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `trend_data_${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }

        // データ更新
        async function refreshData() {
            await loadData();
            alert('データを更新しました');
        }

        // 自動更新（5分ごと）
        setInterval(loadData, 5 * 60 * 1000);

        // ページ読み込み時に実行
        window.addEventListener('DOMContentLoaded', loadData);
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """ダッシュボードを表示"""
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/data')
def get_data():
    """最新のデータをJSON形式で返す（後方互換性のため維持）"""
    try:
        analysis_file = DATA_DIR / 'trends' / 'latest_analysis.json'
        papers_file = DATA_DIR / 'processed' / 'latest_papers.json'

        analysis_data = None
        papers_data = None

        if analysis_file.exists():
            with open(analysis_file, 'r', encoding='utf-8') as f:
                analysis_data = json.load(f)

        if papers_file.exists():
            with open(papers_file, 'r', encoding='utf-8') as f:
                papers_data = json.load(f)

        return jsonify({
            'analysis': analysis_data,
            'papers': papers_data,
            'timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"データ読み込みエラー: {e}")
        return jsonify({
            'error': str(e),
            'analysis': None,
            'papers': None
        })

@app.route('/api/data/full')
def get_full_data():
    """すべてのデータを統合して返す"""
    try:
        result = {
            'papers': {},
            'analysis': None,
            'raw_papers': {},
            'timestamp': datetime.now().isoformat()
        }

        # 最新の生データを優先的に取得（144件のデータ）
        raw_files = sorted(
            (DATA_DIR / 'raw').glob('papers_*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if raw_files:
            with open(raw_files[0], 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                # 生データをメインのpapersとして設定
                result['papers'] = raw_data
                result['raw_papers'] = raw_data

        # 処理済みデータも取得（要約がある場合）
        processed_files = sorted(
            (DATA_DIR / 'processed').glob('summarized_*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if processed_files:
            with open(processed_files[0], 'r', encoding='utf-8') as f:
                summarized = json.load(f)
                # 要約データがある場合は、各論文に追加
                for keyword in result['papers']:
                    if keyword in summarized and isinstance(summarized[keyword], list):
                        # 要約データのマージ（PMIDで照合）
                        for i, paper in enumerate(result['papers'][keyword]):
                            if i < len(summarized[keyword]):
                                if 'ai_summary' in summarized[keyword][i]:
                                    paper['ai_summary'] = summarized[keyword][i]['ai_summary']

        # 最新の分析結果を取得
        analysis_files = sorted(
            (DATA_DIR / 'trends').glob('analysis_*.json'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )

        if analysis_files:
            with open(analysis_files[0], 'r', encoding='utf-8') as f:
                result['analysis'] = json.load(f)

        return jsonify(result)

    except Exception as e:
        logger.error(f"データ読み込みエラー: {e}")
        return jsonify({
            'error': str(e),
            'papers': {},
            'analysis': None,
            'raw_papers': {},
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/data/filtered')
def get_filtered_data():
    """フィルタリングされたデータを返す"""
    try:
        # クエリパラメータを取得
        period = request.args.get('period', 'all')
        keyword = request.args.get('keyword', 'all')

        # フルデータを取得
        full_data = get_full_data().get_json()

        # フィルタリング
        if period != 'all':
            days = int(period)
            cutoff_date = datetime.now() - timedelta(days=days)

            # 論文を日付でフィルタリング
            for key in full_data['papers'].keys():
                full_data['papers'][key] = [
                    paper for paper in full_data['papers'][key]
                    if datetime.fromisoformat(paper.get('publication_date', '2000-01-01')) >= cutoff_date
                ]

        if keyword != 'all':
            # 特定のキーワードのみを返す
            filtered_papers = {}
            if keyword in full_data['papers']:
                filtered_papers[keyword] = full_data['papers'][keyword]
            full_data['papers'] = filtered_papers

        return jsonify(full_data)

    except Exception as e:
        logger.error(f"フィルタリングエラー: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/status')
def status():
    """システムステータスを返す"""
    return jsonify({
        'status': 'running',
        'version': '2.0',
        'data_dir': str(DATA_DIR),
        'features': {
            'period_filter': True,
            'keyword_filter': True,
            'raw_data_view': True,
            'statistics_view': True
        },
        'files': {
            'raw_data': list((DATA_DIR / 'raw').glob('papers_*.json')),
            'processed_data': list((DATA_DIR / 'processed').glob('summarized_*.json')),
            'analysis': list((DATA_DIR / 'trends').glob('analysis_*.json'))
        }
    })

def open_browser():
    """ブラウザを自動で開く"""
    time.sleep(1.5)
    webbrowser.open(f'http://localhost:{DASHBOARD_PORT}')

def main():
    """メインエントリーポイント"""
    logger.info("=" * 50)
    logger.info("🌐 改良版ローカルダッシュボードサーバーを起動します")
    logger.info(f"URL: http://localhost:{DASHBOARD_PORT}")
    logger.info("終了するには Ctrl+C を押してください")
    logger.info("=" * 50)

    # ブラウザを自動で開く
    if AUTO_OPEN_BROWSER:
        thread = threading.Thread(target=open_browser)
        thread.daemon = True
        thread.start()

    # サーバー起動
    app.run(host='0.0.0.0', port=DASHBOARD_PORT, debug=False)

if __name__ == '__main__':
    main()