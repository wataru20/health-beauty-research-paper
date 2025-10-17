#!/usr/bin/env python3
"""
大規模論文データ収集スクリプト
美容・健康分野の論文を大量に収集
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import argparse

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.collectors.pubmed_collector import PubMedCollector

# 環境変数を読み込み
load_dotenv()

# 拡張キーワードセット（美容・健康関連の包括的リスト）
EXPANDED_KEYWORDS = {
    # 既存のキーワード
    "core": [
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
    ],

    # スキンケア成分
    "skincare_ingredients": [
        "retinoid wrinkle",
        "salicylic acid acne",
        "glycolic acid exfoliation",
        "lactic acid moisturizing",
        "vitamin E skin protection",
        "resveratrol antioxidant skin",
        "bakuchiol retinol alternative",
        "tranexamic acid melasma",
        "azelaic acid rosacea",
        "centella asiatica healing"
    ],

    # アンチエイジング
    "anti_aging": [
        "NAD+ longevity",
        "sirtuin activation aging",
        "telomerase anti-aging",
        "growth factor skin rejuvenation",
        "stem cell cosmetics",
        "autophagy skin aging",
        "senolytic compounds",
        "mitochondrial dysfunction aging",
        "oxidative stress skin aging",
        "collagen synthesis stimulation"
    ],

    # 美容サプリメント
    "beauty_supplements": [
        "biotin hair growth",
        "omega-3 skin health",
        "probiotics skin microbiome",
        "astaxanthin UV protection",
        "coenzyme Q10 wrinkle",
        "glutathione skin whitening",
        "zinc acne treatment",
        "vitamin D skin health",
        "curcumin anti-inflammatory skin",
        "green tea polyphenols skin"
    ],

    # 先進的トリートメント
    "advanced_treatments": [
        "microneedling collagen induction",
        "LED therapy skin rejuvenation",
        "radiofrequency skin tightening",
        "platelet-rich plasma facial",
        "mesotherapy skin treatment",
        "cryotherapy anti-aging",
        "ultrasound skin therapy",
        "laser resurfacing wrinkle",
        "chemical peel rejuvenation",
        "dermabrasion skin texture"
    ],

    # 天然・オーガニック成分
    "natural_ingredients": [
        "aloe vera skin healing",
        "tea tree oil acne",
        "rosehip oil scar treatment",
        "jojoba oil moisturizer",
        "argan oil anti-aging",
        "manuka honey wound healing",
        "turmeric skin inflammation",
        "ginseng skin vitality",
        "licorice root pigmentation",
        "chamomile sensitive skin"
    ]
}

class MassDataCollector:
    """大規模データ収集クラス"""

    def __init__(self):
        self.collector = PubMedCollector(api_key=os.getenv('NCBI_API_KEY'))
        self.data_dir = Path('./data/mass_collection')
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def collect_batch(self, keywords, years_back=5, papers_per_keyword=50):
        """
        バッチでデータ収集

        Args:
            keywords: キーワードリスト
            years_back: 遡る年数
            papers_per_keyword: キーワードあたりの最大論文数
        """
        all_results = {}
        total_papers = 0

        end_date = datetime(2024, 9, 24)
        start_date = end_date - timedelta(days=365 * years_back)

        print(f"\n📚 データ収集開始")
        print(f"期間: {start_date.strftime('%Y/%m/%d')} 〜 {end_date.strftime('%Y/%m/%d')}")
        print(f"キーワード数: {len(keywords)}")
        print(f"最大論文数/キーワード: {papers_per_keyword}")
        print("="*60)

        for idx, keyword in enumerate(keywords, 1):
            print(f"\n[{idx}/{len(keywords)}] {keyword}")

            try:
                # 論文検索
                papers = self.collector.search_and_fetch(
                    keyword,
                    max_results=papers_per_keyword,
                    start_date=start_date,
                    end_date=end_date
                )

                if papers:
                    all_results[keyword] = papers
                    total_papers += len(papers)
                    print(f"  ✅ {len(papers)}件収集")
                else:
                    print(f"  ⚠️ データなし")

                # レート制限対策
                time.sleep(0.5)

                # 進捗保存（10キーワードごと）
                if idx % 10 == 0:
                    self._save_checkpoint(all_results, idx)

            except Exception as e:
                print(f"  ❌ エラー: {e}")
                continue

        return all_results, total_papers

    def _save_checkpoint(self, data, checkpoint_num):
        """チェックポイント保存"""
        checkpoint_file = self.data_dir / f"checkpoint_{checkpoint_num}.json"
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  💾 チェックポイント保存: {checkpoint_file.name}")

    def save_results(self, data, total_papers):
        """結果を保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # メインデータファイル
        output_file = self.data_dir / f"papers_mass_{timestamp}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # 統計情報ファイル
        stats_file = self.data_dir / f"stats_{timestamp}.json"
        stats = {
            "timestamp": timestamp,
            "total_papers": total_papers,
            "total_keywords": len(data),
            "papers_per_keyword": {k: len(v) for k, v in data.items()},
            "date_range": self._get_date_range(data)
        }
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        return output_file, stats_file

    def _get_date_range(self, data):
        """データの日付範囲を取得"""
        all_dates = []
        for papers in data.values():
            for paper in papers:
                if 'publication_date' in paper:
                    all_dates.append(paper['publication_date'])

        if all_dates:
            all_dates.sort()
            return {
                "earliest": all_dates[0],
                "latest": all_dates[-1],
                "total_days": (datetime.fromisoformat(all_dates[-1]) -
                              datetime.fromisoformat(all_dates[0])).days
            }
        return None


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='大規模論文データ収集')
    parser.add_argument('--category', default='core',
                       choices=list(EXPANDED_KEYWORDS.keys()) + ['all'],
                       help='収集するキーワードカテゴリ')
    parser.add_argument('--years', type=int, default=5,
                       help='遡る年数')
    parser.add_argument('--max-papers', type=int, default=50,
                       help='キーワードあたりの最大論文数')

    args = parser.parse_args()

    # キーワード選択
    if args.category == 'all':
        keywords = []
        for category_keywords in EXPANDED_KEYWORDS.values():
            keywords.extend(category_keywords)
    else:
        keywords = EXPANDED_KEYWORDS[args.category]

    print("="*60)
    print("🚀 大規模論文データ収集システム")
    print("="*60)
    print(f"カテゴリ: {args.category}")
    print(f"期間: 過去{args.years}年")
    print(f"予想収集数: 最大{len(keywords) * args.max_papers}件")

    # 収集実行
    collector = MassDataCollector()
    results, total = collector.collect_batch(
        keywords,
        years_back=args.years,
        papers_per_keyword=args.max_papers
    )

    # 結果保存
    if results:
        data_file, stats_file = collector.save_results(results, total)

        print("\n" + "="*60)
        print("✅ 収集完了!")
        print(f"総論文数: {total}件")
        print(f"成功キーワード: {len(results)}/{len(keywords)}")
        print(f"データファイル: {data_file}")
        print(f"統計ファイル: {stats_file}")
        print("="*60)
    else:
        print("\n❌ データ収集に失敗しました")


if __name__ == "__main__":
    main()