#!/usr/bin/env python3
"""
1年分のデータを収集するスクリプト（簡易版）
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.collectors.pubmed_collector import PubMedCollector
from src.analyzers.paper_summarizer import PaperSummarizer

# 環境変数を読み込み
load_dotenv()

def main():
    """1年分のデータを収集"""

    print("🚀 1年分のデータ収集を開始します")
    print("="*50)

    # ディレクトリ作成
    data_dir = Path('./data')
    (data_dir / "raw").mkdir(parents=True, exist_ok=True)
    (data_dir / "processed").mkdir(parents=True, exist_ok=True)
    (data_dir / "trends").mkdir(parents=True, exist_ok=True)

    # 主要キーワード（5つに絞る）
    keywords = [
        "NMN anti-aging",
        "collagen supplement skin",
        "hyaluronic acid hydration",
        "CBD inflammation",
        "exosome regeneration"
    ]

    # API設定
    ncbi_api_key = os.getenv('NCBI_API_KEY')
    gemini_api_key = os.getenv('GEMINI_API_KEY')

    if not gemini_api_key:
        print("❌ Gemini APIキーが設定されていません")
        return

    # 日付範囲（過去1年）
    end_date = datetime(2024, 9, 24)
    start_date = end_date - timedelta(days=365)

    print(f"📅 検索期間: {start_date.strftime('%Y/%m/%d')} 〜 {end_date.strftime('%Y/%m/%d')}")

    # 論文収集
    collector = PubMedCollector(api_key=ncbi_api_key)
    all_papers = {}

    for idx, keyword in enumerate(keywords, 1):
        print(f"収集中 [{idx}/{len(keywords)}] {keyword}...", end=" ")

        # 各キーワードで最大10件収集
        papers = collector.search_and_fetch(
            keyword,
            max_results=10,
            start_date=start_date,
            end_date=end_date
        )

        print(f"→ {len(papers)}件")

        if papers:
            all_papers[keyword] = papers

    # 保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    raw_file = data_dir / "raw" / f"papers_1year_{timestamp}.json"

    with open(raw_file, 'w', encoding='utf-8') as f:
        json.dump(all_papers, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 収集完了: {sum(len(papers) for papers in all_papers.values())}件の論文")

    # AI要約
    print("\n🤖 AI要約処理を開始します...")
    summarizer = PaperSummarizer(api_key=gemini_api_key)
    summarized_data = {}

    for keyword, papers in all_papers.items():
        if papers:
            print(f"要約中: {keyword} ({len(papers)}件)")
            # 有効な論文のみフィルタリング
            valid_papers = [p for p in papers if p and isinstance(p, dict) and 'title' in p]
            if valid_papers:
                summarized = summarizer.batch_summarize(valid_papers[:5], max_papers=5)
                summarized_data[keyword] = summarized

    # 要約データ保存
    processed_file = data_dir / "processed" / f"summarized_1year_{timestamp}.json"
    with open(processed_file, 'w', encoding='utf-8') as f:
        json.dump(summarized_data, f, ensure_ascii=False, indent=2)

    # latest_papers.jsonとして保存
    latest_file = data_dir / "processed" / "latest_papers.json"
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(summarized_data, f, ensure_ascii=False, indent=2)

    print(f"✅ 要約完了")

    # トレンド分析
    print("\n📊 トレンド分析中...")
    trend_analysis = summarizer.analyze_trends(summarized_data)

    analysis_file = data_dir / "trends" / f"analysis_1year_{timestamp}.json"
    with open(analysis_file, 'w', encoding='utf-8') as f:
        json.dump(trend_analysis, f, ensure_ascii=False, indent=2)

    # latest_analysis.jsonとして保存
    latest_analysis = data_dir / "trends" / "latest_analysis.json"
    with open(latest_analysis, 'w', encoding='utf-8') as f:
        json.dump(trend_analysis, f, ensure_ascii=False, indent=2)

    print(f"✅ 分析完了")
    print("\n🎉 1年分のデータ収集が完了しました！")

if __name__ == "__main__":
    main()