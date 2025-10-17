#!/usr/bin/env python3
"""
5年分のデータを収集するスクリプト
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.collectors.pubmed_collector import PubMedCollector
from src.analyzers.paper_summarizer import PaperSummarizer

# 環境変数を読み込み
load_dotenv()

def collect_5years_data():
    """5年分のデータを収集"""

    print("🚀 5年分のデータ収集を開始します")
    print("="*50)

    # 設定
    data_dir = Path('./data')
    (data_dir / "raw").mkdir(parents=True, exist_ok=True)
    (data_dir / "processed").mkdir(parents=True, exist_ok=True)
    (data_dir / "trends").mkdir(parents=True, exist_ok=True)

    # キーワード設定
    keywords = [
        "NMN anti-aging",
        "collagen supplement skin",
        "hyaluronic acid hydration",
        "retinol skincare",
        "CBD inflammation",
        "exosome regeneration",
        "peptide anti-aging",
        "niacinamide brightening",
        "ceramide barrier",
        "vitamin C antioxidant"
    ]

    # API設定
    ncbi_api_key = os.getenv('NCBI_API_KEY')
    gemini_api_key = os.getenv('GEMINI_API_KEY')

    if not gemini_api_key:
        print("❌ Gemini APIキーが設定されていません")
        return

    # 期間ごとにデータ収集（1年ずつ5回）
    collector = PubMedCollector(api_key=ncbi_api_key)
    all_papers = {}

    for year in range(5):
        print(f"\n📅 {year}年前のデータを収集中...")

        # 日付範囲を計算
        end_date = datetime(2024, 9, 24) - timedelta(days=365*year)
        start_date = end_date - timedelta(days=365)

        year_papers = {}

        for idx, keyword in enumerate(keywords, 1):
            print(f"  [{idx}/{len(keywords)}] {keyword}", end=" ")

            # 各年で最大3件ずつ収集（合計150件に抑える）
            papers = collector.search_and_fetch(
                keyword,
                max_results=3,
                start_date=start_date,
                end_date=end_date
            )

            print(f"→ {len(papers)}件")

            if papers:
                if keyword not in all_papers:
                    all_papers[keyword] = []
                all_papers[keyword].extend(papers)

            # レート制限対策
            time.sleep(0.5)

    # データ保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_file = data_dir / "raw" / f"papers_5years_{timestamp}.json"

    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 収集完了: {sum(len(papers) for papers in all_papers.values())}件の論文")
    print(f"📁 保存先: {raw_file}")

    # Gemini APIで要約
    print("\n🤖 AI要約処理を開始します...")
    summarizer = PaperSummarizer(api_key=gemini_api_key)
    summarized_data = {}

    for keyword, papers in all_papers.items():
        if papers:
            print(f"要約中: {keyword} ({len(papers)}件)")
            # 最大10件まで要約
            summarized = summarizer.batch_summarize(papers[:10], max_papers=10)
            summarized_data[keyword] = summarized

    # 要約データ保存
    processed_file = data_dir / "processed" / f"summarized_5years_{timestamp}.json"
    with open(processed_file, 'w', encoding='utf-8') as f:
        json.dump(summarized_data, f, ensure_ascii=False, indent=2)

    # latest_papers.jsonとして保存（ダッシュボード用）
    latest_file = data_dir / "processed" / "latest_papers.json"
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(summarized_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 要約完了: {processed_file}")

    # トレンド分析
    print("\n📊 トレンド分析中...")
    trend_analysis = summarizer.analyze_trends(summarized_data)

    analysis_file = data_dir / "trends" / f"analysis_5years_{timestamp}.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(trend_analysis, f, ensure_ascii=False, indent=2)

    # latest_analysis.jsonとして保存
    latest_analysis = data_dir / "trends" / "latest_analysis.json"
    with open(latest_analysis, 'w', encoding='utf-8') as f:
        json.dump(trend_analysis, f, ensure_ascii=False, indent=2)

    print(f"✅ 分析完了: {analysis_file}")
    print("\n🎉 5年分のデータ収集が完了しました！")

if __name__ == "__main__":
    # PubMedCollectorの修正が必要
    # search_and_fetchメソッドを追加

    # まず、PubMedCollectorにメソッドを追加
    import inspect
    from src.collectors.pubmed_collector import PubMedCollector

    # メソッドが存在しない場合は追加
    if not hasattr(PubMedCollector, 'search_and_fetch'):
        def search_and_fetch(self, query, max_results=10, start_date=None, end_date=None):
            """検索と取得を一括で行う"""
            # 日付範囲の計算
            if end_date is None:
                end_date = datetime(2024, 9, 24)
            if start_date is None:
                start_date = end_date - timedelta(days=30)

            days_back = (end_date - start_date).days

            # 検索
            pmids = self.search_papers(query, max_results, days_back)

            # 詳細取得
            if pmids:
                papers = self.fetch_paper_details(pmids)
                return papers
            return []

        # メソッドを動的に追加
        PubMedCollector.search_and_fetch = search_and_fetch

    # データ収集を実行
    collect_5years_data()