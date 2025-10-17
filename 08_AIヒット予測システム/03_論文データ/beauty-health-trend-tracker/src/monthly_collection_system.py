#!/usr/bin/env python3
"""
月次大量データ収集・管理システム
初回は10年分の全データを収集、以降は月次で新規データのみ追加
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import argparse
import hashlib

sys.path.append(str(Path(__file__).parent.parent))
from src.collectors.pubmed_collector import PubMedCollector

# 環境変数を読み込み
load_dotenv()

# データベースディレクトリ
DATABASE_DIR = Path('./database')
DATABASE_DIR.mkdir(exist_ok=True)

class MonthlyCollectionSystem:
    """月次収集システム"""

    def __init__(self):
        self.collector = PubMedCollector(api_key=os.getenv('NCBI_API_KEY'))
        self.master_db = DATABASE_DIR / 'master_papers.json'
        self.meta_db = DATABASE_DIR / 'metadata.json'
        self.monthly_dir = DATABASE_DIR / 'monthly_updates'
        self.monthly_dir.mkdir(exist_ok=True)

        # 拡張キーワードリスト（全60キーワード）
        self.all_keywords = self._get_all_keywords()

    def _get_all_keywords(self):
        """全キーワードリストを取得"""
        return [
            # Core (10)
            "NMN anti-aging", "collagen supplement skin", "hyaluronic acid hydration",
            "retinol skincare", "CBD inflammation", "exosome regeneration",
            "peptide anti-aging", "niacinamide brightening", "ceramide barrier",
            "vitamin C antioxidant",

            # Skincare ingredients (10)
            "retinoid wrinkle", "salicylic acid acne", "glycolic acid exfoliation",
            "lactic acid moisturizing", "vitamin E skin protection",
            "resveratrol antioxidant skin", "bakuchiol retinol alternative",
            "tranexamic acid melasma", "azelaic acid rosacea", "centella asiatica healing",

            # Anti-aging (10)
            "NAD+ longevity", "sirtuin activation aging", "telomerase anti-aging",
            "growth factor skin rejuvenation", "stem cell cosmetics",
            "autophagy skin aging", "senolytic compounds",
            "mitochondrial dysfunction aging", "oxidative stress skin aging",
            "collagen synthesis stimulation",

            # Beauty supplements (10)
            "biotin hair growth", "omega-3 skin health", "probiotics skin microbiome",
            "astaxanthin UV protection", "coenzyme Q10 wrinkle",
            "glutathione skin whitening", "zinc acne treatment",
            "vitamin D skin health", "curcumin anti-inflammatory skin",
            "green tea polyphenols skin",

            # Advanced treatments (10)
            "microneedling collagen induction", "LED therapy skin rejuvenation",
            "radiofrequency skin tightening", "platelet-rich plasma facial",
            "mesotherapy skin treatment", "cryotherapy anti-aging",
            "ultrasound skin therapy", "laser resurfacing wrinkle",
            "chemical peel rejuvenation", "dermabrasion skin texture",

            # Natural ingredients (10)
            "aloe vera skin healing", "tea tree oil acne", "rosehip oil scar treatment",
            "jojoba oil moisturizer", "argan oil anti-aging",
            "manuka honey wound healing", "turmeric skin inflammation",
            "ginseng skin vitality", "licorice root pigmentation",
            "chamomile sensitive skin"
        ]

    def initial_massive_collection(self, years=10, papers_per_keyword=100):
        """
        初回の大量データ収集（10年分）

        Args:
            years: 遡る年数（デフォルト10年）
            papers_per_keyword: キーワードあたりの最大論文数
        """
        print("="*70)
        print("📚 初回大量データ収集を開始します")
        print(f"期間: 過去{years}年")
        print(f"キーワード数: {len(self.all_keywords)}")
        print(f"最大予想論文数: {len(self.all_keywords) * papers_per_keyword}")
        print("="*70)

        # マスターデータベース初期化
        if self.master_db.exists():
            print("\n⚠️ 既存のマスターデータベースが存在します")
            with open(self.master_db, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                print(f"  既存データ: {len(existing_data)}件")
        else:
            existing_data = {}

        # 収集期間設定
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * years)

        collected_count = 0
        error_count = 0

        print(f"\n収集開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        for idx, keyword in enumerate(self.all_keywords, 1):
            print(f"\n[{idx}/{len(self.all_keywords)}] {keyword}")

            try:
                # 論文検索
                papers = self.collector.search_and_fetch(
                    keyword,
                    max_results=papers_per_keyword,
                    start_date=start_date,
                    end_date=end_date
                )

                if papers:
                    # 重複チェックとマージ
                    new_papers = 0
                    for paper in papers:
                        paper_id = self._generate_paper_id(paper)
                        if paper_id not in existing_data:
                            existing_data[paper_id] = paper
                            existing_data[paper_id]['keywords'] = [keyword]
                            existing_data[paper_id]['collected_at'] = datetime.now().isoformat()
                            new_papers += 1
                        elif keyword not in existing_data[paper_id].get('keywords', []):
                            existing_data[paper_id]['keywords'].append(keyword)

                    collected_count += new_papers
                    print(f"  ✅ {len(papers)}件取得 (新規: {new_papers}件)")
                else:
                    print(f"  ⚠️ データなし")

                # 10キーワードごとに保存
                if idx % 10 == 0:
                    self._save_master_database(existing_data)
                    print(f"  💾 チェックポイント保存 (総数: {len(existing_data)}件)")

                # レート制限対策
                time.sleep(0.1)  # APIキーありなので高速

            except Exception as e:
                print(f"  ❌ エラー: {e}")
                error_count += 1
                continue

        # 最終保存
        self._save_master_database(existing_data)

        # メタデータ更新
        self._update_metadata({
            'last_full_collection': datetime.now().isoformat(),
            'total_papers': len(existing_data),
            'total_keywords': len(self.all_keywords),
            'collection_years': years,
            'errors': error_count
        })

        print("\n" + "="*70)
        print("✅ 初回大量収集完了！")
        print(f"総論文数: {len(existing_data)}件")
        print(f"新規追加: {collected_count}件")
        print(f"エラー: {error_count}件")
        print(f"完了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)

        return existing_data

    def monthly_update(self):
        """
        月次更新（過去1ヶ月の新規データのみ収集）
        """
        print("="*70)
        print("📅 月次更新を開始します")
        print("="*70)

        # 既存データ読み込み
        if not self.master_db.exists():
            print("❌ マスターデータベースが存在しません")
            print("初回収集を実行してください")
            return None

        with open(self.master_db, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)

        print(f"既存データ: {len(existing_data)}件")

        # 過去30日分のみ収集
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)

        monthly_data = {}
        new_count = 0

        for idx, keyword in enumerate(self.all_keywords, 1):
            print(f"[{idx}/{len(self.all_keywords)}] {keyword}", end=" ")

            try:
                # 新規論文のみ検索（最大20件）
                papers = self.collector.search_and_fetch(
                    keyword,
                    max_results=20,
                    start_date=start_date,
                    end_date=end_date
                )

                if papers:
                    new_papers = 0
                    for paper in papers:
                        paper_id = self._generate_paper_id(paper)
                        if paper_id not in existing_data:
                            monthly_data[paper_id] = paper
                            monthly_data[paper_id]['keywords'] = [keyword]
                            monthly_data[paper_id]['collected_at'] = datetime.now().isoformat()
                            existing_data[paper_id] = monthly_data[paper_id]
                            new_papers += 1

                    new_count += new_papers
                    print(f"→ 新規{new_papers}件")
                else:
                    print("→ 0件")

                time.sleep(0.1)

            except Exception as e:
                print(f"→ エラー")
                continue

        # 保存
        if monthly_data:
            # 月次ファイル保存
            monthly_file = self.monthly_dir / f"update_{datetime.now().strftime('%Y%m')}.json"
            with open(monthly_file, 'w', encoding='utf-8') as f:
                json.dump(monthly_data, f, ensure_ascii=False, indent=2)

            # マスターデータベース更新
            self._save_master_database(existing_data)

            # メタデータ更新
            self._update_metadata({
                'last_monthly_update': datetime.now().isoformat(),
                'monthly_new_papers': new_count,
                'total_papers': len(existing_data)
            })

        print(f"\n✅ 月次更新完了: 新規{new_count}件追加")
        print(f"総論文数: {len(existing_data)}件")

        return monthly_data

    def _generate_paper_id(self, paper):
        """論文の一意IDを生成"""
        # PMIDがあればそれを使用
        if 'pmid' in paper:
            return f"pmid_{paper['pmid']}"
        # なければタイトルと著者からハッシュ生成
        text = f"{paper.get('title', '')}{paper.get('authors', [])}"
        return hashlib.md5(text.encode()).hexdigest()

    def _save_master_database(self, data):
        """マスターデータベースを保存"""
        with open(self.master_db, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _update_metadata(self, updates):
        """メタデータを更新"""
        if self.meta_db.exists():
            with open(self.meta_db, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        metadata.update(updates)

        with open(self.meta_db, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def get_statistics(self):
        """統計情報を取得"""
        if not self.master_db.exists():
            return None

        with open(self.master_db, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 年別統計
        year_stats = {}
        keyword_stats = {}

        for paper_id, paper in data.items():
            # 年別
            if 'publication_date' in paper:
                year = paper['publication_date'][:4]
                year_stats[year] = year_stats.get(year, 0) + 1

            # キーワード別
            for keyword in paper.get('keywords', []):
                keyword_stats[keyword] = keyword_stats.get(keyword, 0) + 1

        return {
            'total_papers': len(data),
            'year_distribution': year_stats,
            'keyword_distribution': keyword_stats,
            'database_size_mb': self.master_db.stat().st_size / (1024 * 1024)
        }


def main():
    parser = argparse.ArgumentParser(description='月次大量データ収集システム')
    parser.add_argument('--mode', choices=['initial', 'update', 'stats'],
                       default='stats', help='実行モード')
    parser.add_argument('--years', type=int, default=10,
                       help='初回収集の年数')
    parser.add_argument('--max-papers', type=int, default=100,
                       help='キーワードあたりの最大論文数')

    args = parser.parse_args()

    system = MonthlyCollectionSystem()

    if args.mode == 'initial':
        # 初回大量収集
        system.initial_massive_collection(
            years=args.years,
            papers_per_keyword=args.max_papers
        )

    elif args.mode == 'update':
        # 月次更新
        system.monthly_update()

    elif args.mode == 'stats':
        # 統計表示
        stats = system.get_statistics()
        if stats:
            print("\n📊 データベース統計")
            print("="*50)
            print(f"総論文数: {stats['total_papers']:,}件")
            print(f"データベースサイズ: {stats['database_size_mb']:.1f} MB")
            print("\n年別分布:")
            for year in sorted(stats['year_distribution'].keys()):
                count = stats['year_distribution'][year]
                print(f"  {year}年: {count:,}件")
            print("\nキーワード別TOP10:")
            for keyword, count in sorted(stats['keyword_distribution'].items(),
                                        key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {keyword}: {count}件")
        else:
            print("データベースが存在しません")


if __name__ == "__main__":
    main()