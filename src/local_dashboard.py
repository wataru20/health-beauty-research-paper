#!/usr/bin/env python3
"""
ローカルダッシュボードサーバー
Flaskを使用してダッシュボードをローカルで表示
"""

import os
import json
import logging
from flask import Flask, render_template_string, jsonify, send_from_directory
from pathlib import Path
from datetime import datetime
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
DASHBOARD_PORT = int(os.getenv('DASHBOARD_PORT', 8080))
AUTO_OPEN_BROWSER = os.getenv('AUTO_OPEN_BROWSER', 'true').lower() == 'true'

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ダッシュボードHTMLテンプレート（改良版）
DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>美容・健康成分トレンド分析ダッシュボード (ローカル版)</title>
    
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
    </style>
</head>
<body class="bg-gray-50">
    <!-- ヘッダー -->
    <header class="gradient-bg text-white p-6 shadow-lg">
        <div class="container mx-auto">
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-3xl font-bold">🧬 美容・健康成分トレンド分析</h1>
                    <p class="mt-2 text-purple-100">ローカル環境版 - PubMed論文データ分析</p>
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

    <!-- メインコンテンツ -->
    <main class="container mx-auto p-6">
        <!-- エラーメッセージ -->
        <div id="errorMessage" class="hidden bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong>エラー:</strong> <span id="errorText"></span>
        </div>

        <!-- サマリーカード -->
        <div class="grid md:grid-cols-4 gap-4 mb-8">
            <div class="card bg-white rounded-lg shadow-md p-6">
                <div class="flex items-center justify-between">
                    <div>
                        <p class="text-gray-600 text-sm">新着論文</p>
                        <p class="text-3xl font-bold text-purple-600" id="weeklyPapers">-</p>
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

        <!-- トレンドインサイト -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 class="text-xl font-bold mb-4 text-gray-800">💡 トレンドインサイト</h2>
            <ul id="insightsList" class="space-y-2 text-gray-700">
                <li class="loading">データを読み込み中...</li>
            </ul>
        </div>

        <!-- 論文リスト -->
        <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-bold mb-4 text-gray-800">📚 最新論文（AI要約付き）</h2>
            <div id="papersList" class="space-y-4">
                <p class="text-gray-500 loading">論文を読み込み中...</p>
            </div>
        </div>
    </main>

    <!-- フッター -->
    <footer class="bg-gray-800 text-white p-4 mt-12">
        <div class="container mx-auto text-center text-sm">
            <p>© 2024 Beauty & Health Trend Tracker (Local) | Powered by PubMed E-utilities & Gemini API</p>
            <p class="mt-2 text-gray-400">実行環境: ローカル | ポート: {{ port }}</p>
        </div>
    </footer>

    <script>
        // グローバル変数
        let keywordChart = null;
        let ingredientChart = null;
        
        // データ読み込み
        async function loadData() {
            try {
                // ローディング表示
                document.querySelectorAll('.loading').forEach(el => {
                    el.style.animation = 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite';
                });
                
                // APIからデータ取得
                const response = await fetch('/api/data');
                const data = await response.json();
                
                if (data.error) {
                    showError(data.error);
                    return;
                }
                
                // ダッシュボード更新
                updateDashboard(data.analysis, data.papers);
                
                // エラーメッセージを隠す
                document.getElementById('errorMessage').classList.add('hidden');
                
            } catch (error) {
                console.error('データ読み込みエラー:', error);
                showError('データの読み込みに失敗しました。サーバーが起動していることを確認してください。');
            } finally {
                // ローディング解除
                document.querySelectorAll('.loading').forEach(el => {
                    el.style.animation = 'none';
                });
            }
        }
        
        // エラー表示
        function showError(message) {
            document.getElementById('errorText').textContent = message;
            document.getElementById('errorMessage').classList.remove('hidden');
        }
        
        // ダッシュボード更新
        function updateDashboard(analysis, papers) {
            if (!analysis) {
                showError('分析データが見つかりません。まずデータ収集を実行してください。');
                return;
            }
            
            // サマリー更新
            document.getElementById('lastUpdate').textContent = 
                `最終更新: ${new Date(analysis.analysis_date).toLocaleString('ja-JP')}`;
            document.getElementById('totalPapers').textContent = 
                `総論文数: ${analysis.total_papers_analyzed || 0}件`;
            
            // 統計情報
            document.getElementById('weeklyPapers').textContent = 
                analysis.total_papers_analyzed || '0';
            
            // キーワード数
            const keywordCount = Object.keys(analysis.keyword_analysis || {}).length;
            document.getElementById('keywordCount').textContent = keywordCount;
            
            // トップ成分
            if (analysis.top_ingredients && analysis.top_ingredients.length > 0) {
                document.getElementById('topIngredient').textContent = 
                    analysis.top_ingredients[0].name;
            }
            
            // 平均重要度
            let totalImportance = 0;
            let count = 0;
            for (const keyword in analysis.keyword_analysis || {}) {
                totalImportance += analysis.keyword_analysis[keyword].avg_importance;
                count++;
            }
            document.getElementById('avgImportance').textContent = 
                count > 0 ? (totalImportance / count).toFixed(1) : '0.0';
            
            // グラフ更新
            updateCharts(analysis);
            
            // インサイト更新
            updateInsights(analysis.trend_insights || []);
            
            // 論文リスト更新
            updatePapersList(papers);
        }
        
        // グラフ更新
        function updateCharts(analysis) {
            // キーワード別論文数
            const keywordLabels = [];
            const keywordData = [];
            
            for (const keyword in analysis.keyword_analysis || {}) {
                keywordLabels.push(keyword);
                keywordData.push(analysis.keyword_analysis[keyword].paper_count);
            }
            
            const keywordCtx = document.getElementById('keywordChart').getContext('2d');
            if (keywordChart) keywordChart.destroy();
            keywordChart = new Chart(keywordCtx, {
                type: 'bar',
                data: {
                    labels: keywordLabels,
                    datasets: [{
                        label: '論文数',
                        data: keywordData,
                        backgroundColor: 'rgba(147, 51, 234, 0.5)',
                        borderColor: 'rgba(147, 51, 234, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
            
            // 成分出現頻度
            const ingredients = analysis.top_ingredients || [];
            const ingredientLabels = ingredients.slice(0, 10).map(i => i.name);
            const ingredientData = ingredients.slice(0, 10).map(i => i.count);
            
            const ingredientCtx = document.getElementById('ingredientChart').getContext('2d');
            if (ingredientChart) ingredientChart.destroy();
            
            if (ingredientLabels.length > 0) {
                ingredientChart = new Chart(ingredientCtx, {
                    type: 'doughnut',
                    data: {
                        labels: ingredientLabels,
                        datasets: [{
                            data: ingredientData,
                            backgroundColor: [
                                '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                                '#9966FF', '#FF9F40', '#FF6B6B', '#4ECDC4',
                                '#45B7D1', '#FFA07A'
                            ]
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'right'
                            }
                        }
                    }
                });
            }
        }
        
        // インサイト更新
        function updateInsights(insights) {
            const list = document.getElementById('insightsList');
            
            if (insights.length === 0) {
                list.innerHTML = '<li class="text-gray-500">インサイトはまだありません</li>';
                return;
            }
            
            list.innerHTML = insights.map(insight => 
                `<li class="flex items-start">
                    <span class="text-purple-500 mr-2">•</span>
                    <span>${insight}</span>
                </li>`
            ).join('');
        }
        
        // 論文リスト更新
        function updatePapersList(papers) {
            const list = document.getElementById('papersList');
            
            if (!papers) {
                list.innerHTML = '<p class="text-gray-500">論文データがありません</p>';
                return;
            }
            
            let allPapers = [];
            
            // 全論文を収集
            for (const keyword in papers) {
                allPapers = allPapers.concat(papers[keyword]);
            }
            
            if (allPapers.length === 0) {
                list.innerHTML = '<p class="text-gray-500">論文が見つかりません</p>';
                return;
            }
            
            // 重要度でソート
            allPapers.sort((a, b) => {
                const scoreA = a.ai_summary?.importance_score || 0;
                const scoreB = b.ai_summary?.importance_score || 0;
                return scoreB - scoreA;
            });
            
            // 上位10件を表示
            const topPapers = allPapers.slice(0, 10);
            
            list.innerHTML = topPapers.map(paper => `
                <div class="border-l-4 border-purple-500 pl-4 hover:bg-gray-50 transition">
                    <h3 class="font-bold text-gray-800 mb-1">
                        ${paper.title || 'タイトルなし'}
                    </h3>
                    <p class="text-sm text-gray-600 mb-2">
                        ${paper.ai_summary?.summary_jp || '要約なし'}
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
                        <a href="${paper.url}" target="_blank" 
                           class="text-purple-600 hover:underline">
                            PubMedで見る →
                        </a>
                    </div>
                </div>
            `).join('');
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
    return render_template_string(DASHBOARD_HTML, port=DASHBOARD_PORT)

@app.route('/api/data')
def get_data():
    """最新のデータをJSON形式で返す"""
    try:
        # 最新の分析結果を読み込み
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

@app.route('/api/status')
def status():
    """システムステータスを返す"""
    return jsonify({
        'status': 'running',
        'data_dir': str(DATA_DIR),
        'files': {
            'analysis': (DATA_DIR / 'trends' / 'latest_analysis.json').exists(),
            'papers': (DATA_DIR / 'processed' / 'latest_papers.json').exists()
        }
    })

def open_browser():
    """ブラウザを自動で開く"""
    time.sleep(1.5)  # サーバー起動を待つ
    webbrowser.open(f'http://localhost:{DASHBOARD_PORT}')

def main():
    """メインエントリーポイント"""
    logger.info("=" * 50)
    logger.info("🌐 ローカルダッシュボードサーバーを起動します")
    logger.info(f"URL: http://localhost:{DASHBOARD_PORT}")
    logger.info("終了するには Ctrl+C を押してください")
    logger.info("=" * 50)
    
    # ブラウザを自動で開く
    if AUTO_OPEN_BROWSER:
        threading.Thread(target=open_browser).start()
    
    # Flaskサーバー起動
    app.run(
        host='0.0.0.0',
        port=DASHBOARD_PORT,
        debug=False
    )

if __name__ == '__main__':
    main()
