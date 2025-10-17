#!/usr/bin/env python3
"""
データ収集・処理フロー分析スクリプト
実際のデータを分析して可視化レポートを生成
"""

import json
import glob
from datetime import datetime
from collections import Counter, defaultdict
import os

print("="*70)
print(" 📊 美容・健康トレンド追跡システム - データフロー分析レポート")
print("="*70)

# 1. データ収集フェーズの分析
print("\n" + "="*50)
print("📥 【Phase 1: データ収集】")
print("="*50)

# 収集済みデータの分析
raw_files = sorted(glob.glob('data/raw/*.json'))
print(f"\n収集済みファイル数: {len(raw_files)}")

for f in raw_files[-3:]:  # 最新3ファイル
    with open(f) as fp:
        data = json.load(fp)
        filename = os.path.basename(f)
        total_papers = sum(len(v) if isinstance(v, list) else 0 for v in data.values())

        print(f"\n📄 {filename}")
        print(f"   総論文数: {total_papers}件")
        print(f"   キーワード数: {len(data)}")

        # サンプルデータ表示
        if data:
            first_key = list(data.keys())[0]
            if data[first_key] and isinstance(data[first_key], list):
                sample = data[first_key][0]
                print(f"   サンプルデータ構造:")
                for key in list(sample.keys())[:5]:
                    value = str(sample[key])[:50] + "..." if len(str(sample[key])) > 50 else str(sample[key])
                    print(f"      - {key}: {value}")

# 最新の5年分データを詳細分析
five_year_file = 'data/raw/papers_5years_20250924_111234.json'
if os.path.exists(five_year_file):
    print(f"\n🔍 詳細分析: {os.path.basename(five_year_file)}")
    with open(five_year_file) as fp:
        data = json.load(fp)

        # キーワード別の論文数
        print("\n  キーワード別収集状況:")
        for keyword, papers in data.items():
            if isinstance(papers, list):
                print(f"    • {keyword}: {len(papers)}件")

                # 年別分布
                year_dist = Counter()
                for paper in papers:
                    if 'publication_date' in paper:
                        year = paper['publication_date'][:4]
                        year_dist[year] += 1

                if year_dist:
                    years_str = ", ".join([f"{y}年:{c}件" for y, c in sorted(year_dist.items())])
                    print(f"      年別: {years_str}")

# 2. データ処理フェーズの分析
print("\n" + "="*50)
print("⚙️ 【Phase 2: データ処理】")
print("="*50)

processed_files = sorted(glob.glob('data/processed/*.json'))
print(f"\n処理済みファイル数: {len(processed_files)}")

for f in processed_files:
    filename = os.path.basename(f)

    # ファイルサイズ
    size = os.path.getsize(f)
    size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/(1024*1024):.1f}MB"

    try:
        with open(f) as fp:
            data = json.load(fp)
            if isinstance(data, dict):
                total = sum(len(v) if isinstance(v, list) else 0 for v in data.values())

                # AI要約の有無をチェック
                has_summary = False
                if data:
                    for papers in data.values():
                        if isinstance(papers, list) and papers:
                            if 'ai_summary' in papers[0]:
                                has_summary = True
                                break

                status = "✅ AI要約あり" if has_summary else "📄 生データ"
                print(f"\n📄 {filename} ({size_str})")
                print(f"   状態: {status}")
                print(f"   論文数: {total}件")
    except:
        print(f"\n📄 {filename} ({size_str}) - 読み込みエラー")

# 3. データ分析フェーズ
print("\n" + "="*50)
print("📈 【Phase 3: トレンド分析】")
print("="*50)

analysis_files = sorted(glob.glob('data/trends/*.json'))
print(f"\n分析結果ファイル数: {len(analysis_files)}")

for f in analysis_files[-2:]:  # 最新2ファイル
    filename = os.path.basename(f)

    try:
        with open(f) as fp:
            data = json.load(fp)

            print(f"\n📊 {filename}")

            # トレンド分析の内容
            if 'top_keywords' in data:
                print(f"   トップキーワード:")
                for kw in data['top_keywords'][:3]:
                    if isinstance(kw, dict):
                        print(f"      • {kw.get('keyword', 'N/A')}: 重要度 {kw.get('importance', 'N/A')}")

            if 'ingredient_frequency' in data:
                print(f"   成分頻度分析: {len(data['ingredient_frequency'])}種類")
                for ing in data['ingredient_frequency'][:3]:
                    if isinstance(ing, dict):
                        print(f"      • {ing.get('name', 'N/A')}: {ing.get('count', 0)}回出現")

            if 'emerging_trends' in data:
                print(f"   新興トレンド: {len(data['emerging_trends'])}個")
    except:
        print(f"\n📊 {filename} - 読み込みエラー")

# 4. データフロー図
print("\n" + "="*70)
print("🔄 【データ処理フロー図】")
print("="*70)

flow_diagram = """

[1] PubMed API
     ↓
     ↓ 検索クエリ (10キーワード × 最大15件/年 × 5年)
     ↓
[2] 論文メタデータ収集 (papers_5years_*.json)
     ├─ タイトル
     ├─ 著者
     ├─ アブストラクト
     ├─ 発表日
     ├─ PMID
     └─ URL
     ↓
[3] Gemini AI API
     ↓
     ↓ AI要約・分析
     ↓
[4] 要約データ生成 (summarized_*.json)
     ├─ 主要な発見
     ├─ 重要度スコア (0-10)
     ├─ 関連成分
     └─ 応用分野
     ↓
[5] トレンド分析 (analysis_*.json)
     ├─ キーワード別重要度
     ├─ 成分出現頻度
     ├─ 新興トレンド
     └─ 時系列分析
     ↓
[6] ダッシュボード表示
     ├─ 期間フィルター (7日〜5年)
     ├─ キーワードフィルター
     └─ 3つの表示モード
         ├─ 要約ビュー
         ├─ 元データビュー
         └─ 統計ビュー
"""

print(flow_diagram)

# 5. API連携状況
print("="*70)
print("🔌 【API連携状況】")
print("="*70)

# 環境変数チェック
from dotenv import load_dotenv
load_dotenv()

apis = {
    "PubMed (NCBI)": {
        "key": os.getenv('NCBI_API_KEY'),
        "status": "✅ 設定済み" if os.getenv('NCBI_API_KEY') and os.getenv('NCBI_API_KEY') != '' else "⚠️ 未設定（レート制限あり）",
        "用途": "論文検索・メタデータ取得"
    },
    "Google Gemini AI": {
        "key": os.getenv('GEMINI_API_KEY'),
        "status": "✅ 設定済み" if os.getenv('GEMINI_API_KEY') and os.getenv('GEMINI_API_KEY') != 'your_gemini_api_key_here' else "❌ 未設定",
        "用途": "論文要約・トレンド分析"
    }
}

for api_name, info in apis.items():
    print(f"\n{api_name}:")
    print(f"  状態: {info['status']}")
    print(f"  用途: {info['用途']}")

# 6. データ品質分析
print("\n" + "="*70)
print("📊 【データ品質分析】")
print("="*70)

if os.path.exists(five_year_file):
    with open(five_year_file) as fp:
        data = json.load(fp)

        total_papers = sum(len(v) if isinstance(v, list) else 0 for v in data.values())

        # データの完全性チェック
        complete_count = 0
        missing_fields = defaultdict(int)

        for papers in data.values():
            if isinstance(papers, list):
                for paper in papers:
                    # 必須フィールドチェック
                    required = ['title', 'abstract', 'authors', 'publication_date', 'pmid']
                    is_complete = True
                    for field in required:
                        if field not in paper or not paper[field]:
                            missing_fields[field] += 1
                            is_complete = False
                    if is_complete:
                        complete_count += 1

        print(f"\nデータ完全性:")
        print(f"  完全なレコード: {complete_count}/{total_papers} ({complete_count*100/total_papers:.1f}%)")

        if missing_fields:
            print(f"\n  欠損フィールド:")
            for field, count in missing_fields.items():
                print(f"    • {field}: {count}件")

print("\n" + "="*70)
print("✅ 分析完了")
print("="*70)