#!/usr/bin/env python3
"""
バッチ分析システム
大量データを段階的にGemini APIで分析
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import google.generativeai as genai
import argparse

sys.path.append(str(Path(__file__).parent.parent))

# 環境変数を読み込み
load_dotenv()

# データベースディレクトリ
DATABASE_DIR = Path('./database')
ANALYSIS_DIR = DATABASE_DIR / 'analysis'
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

class BatchAnalysisSystem:
    """バッチ分析システム"""

    def __init__(self):
        # Gemini API設定
        self.api_key = os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

        self.master_db = DATABASE_DIR / 'master_papers.json'
        self.analysis_db = ANALYSIS_DIR / 'analyzed_papers.json'
        self.analysis_meta = ANALYSIS_DIR / 'analysis_metadata.json'

    def analyze_batch(self, batch_size=50, max_batches=None):
        """
        バッチ単位で論文を分析

        Args:
            batch_size: 1バッチあたりの論文数
            max_batches: 最大バッチ数（Noneで全て）
        """
        if not self.api_key:
            print("❌ Gemini APIキーが設定されていません")
            return

        # マスターデータベース読み込み
        if not self.master_db.exists():
            print("❌ マスターデータベースが存在しません")
            return

        with open(self.master_db, 'r', encoding='utf-8') as f:
            all_papers = json.load(f)

        # 既に分析済みのデータを読み込み
        if self.analysis_db.exists():
            with open(self.analysis_db, 'r', encoding='utf-8') as f:
                analyzed_papers = json.load(f)
        else:
            analyzed_papers = {}

        # 未分析の論文を抽出
        unanalyzed = {
            pid: paper for pid, paper in all_papers.items()
            if pid not in analyzed_papers
        }

        if not unanalyzed:
            print("✅ すべての論文が分析済みです")
            return

        print("="*70)
        print("🤖 バッチ分析を開始します")
        print(f"総論文数: {len(all_papers):,}件")
        print(f"分析済み: {len(analyzed_papers):,}件")
        print(f"未分析: {len(unanalyzed):,}件")
        print(f"バッチサイズ: {batch_size}件")
        print("="*70)

        # バッチ処理
        paper_ids = list(unanalyzed.keys())
        total_batches = (len(paper_ids) + batch_size - 1) // batch_size

        if max_batches:
            total_batches = min(total_batches, max_batches)

        analyzed_count = 0
        error_count = 0

        for batch_num in range(total_batches):
            batch_start = batch_num * batch_size
            batch_end = min(batch_start + batch_size, len(paper_ids))
            batch_ids = paper_ids[batch_start:batch_end]

            print(f"\n[バッチ {batch_num + 1}/{total_batches}] "
                  f"{len(batch_ids)}件を分析中...")

            for idx, paper_id in enumerate(batch_ids, 1):
                paper = unanalyzed[paper_id]

                try:
                    # 論文を分析
                    analysis = self._analyze_single_paper(paper)

                    if analysis:
                        # 分析結果を保存
                        analyzed_papers[paper_id] = {
                            **paper,
                            'ai_analysis': analysis,
                            'analyzed_at': datetime.now().isoformat()
                        }
                        analyzed_count += 1

                        if idx % 10 == 0:
                            print(f"  進捗: {idx}/{len(batch_ids)}")

                    # API制限対策（1秒待機）
                    time.sleep(1)

                except Exception as e:
                    print(f"  ❌ エラー (ID: {paper_id}): {e}")
                    error_count += 1
                    continue

            # バッチ完了後に保存
            self._save_analyzed_papers(analyzed_papers)
            print(f"  ✅ バッチ{batch_num + 1}完了: {analyzed_count}件分析済み")

            # バッチ間の休憩（10秒）
            if batch_num < total_batches - 1:
                print("  💤 10秒待機中...")
                time.sleep(10)

        # メタデータ更新
        self._update_analysis_metadata({
            'last_analysis': datetime.now().isoformat(),
            'total_analyzed': len(analyzed_papers),
            'latest_batch_analyzed': analyzed_count,
            'errors': error_count
        })

        print("\n" + "="*70)
        print("✅ バッチ分析完了!")
        print(f"新規分析: {analyzed_count}件")
        print(f"総分析済み: {len(analyzed_papers)}件")
        print(f"エラー: {error_count}件")
        print("="*70)

    def _analyze_single_paper(self, paper):
        """単一論文を分析"""
        prompt = f"""
        以下の論文を分析し、美容・健康トレンドの観点から評価してください。

        タイトル: {paper.get('title', 'N/A')}
        要約: {paper.get('abstract', 'N/A')[:1000]}
        発表日: {paper.get('publication_date', 'N/A')}

        以下の項目を日本語で簡潔に回答してください：
        1. 主要な発見（2-3点）
        2. 美容・健康産業への影響度（1-10点）
        3. 実用化の可能性（高/中/低）
        4. 関連する美容成分・技術（最大3つ）
        5. 注目ポイント（1文）
        """

        try:
            response = self.model.generate_content(prompt)
            return self._parse_analysis(response.text)
        except Exception as e:
            print(f"    分析エラー: {e}")
            return None

    def _parse_analysis(self, text):
        """分析結果をパース"""
        # シンプルな構造化（実際の応答に応じて調整）
        return {
            'summary': text[:500],  # 最初の500文字を要約として保存
            'full_analysis': text,
            'analyzed_at': datetime.now().isoformat()
        }

    def _save_analyzed_papers(self, data):
        """分析済みデータを保存"""
        with open(self.analysis_db, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _update_analysis_metadata(self, updates):
        """分析メタデータを更新"""
        if self.analysis_meta.exists():
            with open(self.analysis_meta, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {}

        metadata.update(updates)

        with open(self.analysis_meta, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def generate_trend_report(self):
        """トレンドレポートを生成"""
        if not self.analysis_db.exists():
            print("❌ 分析データが存在しません")
            return

        with open(self.analysis_db, 'r', encoding='utf-8') as f:
            analyzed_papers = json.load(f)

        print("\n" + "="*70)
        print("📊 トレンドレポート生成")
        print("="*70)

        # キーワード別集計
        keyword_stats = {}
        for paper_id, paper in analyzed_papers.items():
            for keyword in paper.get('keywords', []):
                if keyword not in keyword_stats:
                    keyword_stats[keyword] = {
                        'count': 0,
                        'papers': []
                    }
                keyword_stats[keyword]['count'] += 1
                keyword_stats[keyword]['papers'].append(paper_id)

        # レポート生成
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_papers': len(analyzed_papers),
            'keyword_statistics': keyword_stats,
            'top_keywords': sorted(keyword_stats.items(),
                                  key=lambda x: x[1]['count'],
                                  reverse=True)[:10]
        }

        # レポート保存
        report_file = ANALYSIS_DIR / f"trend_report_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"✅ レポート生成完了: {report_file}")
        print(f"\nトップ10キーワード:")
        for keyword, stats in report['top_keywords']:
            print(f"  • {keyword}: {stats['count']}件")

        return report


def main():
    parser = argparse.ArgumentParser(description='バッチ分析システム')
    parser.add_argument('--mode', choices=['analyze', 'report', 'status'],
                       default='status', help='実行モード')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='バッチサイズ')
    parser.add_argument('--max-batches', type=int, default=None,
                       help='最大バッチ数')

    args = parser.parse_args()

    system = BatchAnalysisSystem()

    if args.mode == 'analyze':
        # バッチ分析実行
        system.analyze_batch(
            batch_size=args.batch_size,
            max_batches=args.max_batches
        )

    elif args.mode == 'report':
        # トレンドレポート生成
        system.generate_trend_report()

    elif args.mode == 'status':
        # ステータス表示
        if system.master_db.exists():
            with open(system.master_db, 'r', encoding='utf-8') as f:
                all_papers = json.load(f)
            total = len(all_papers)
        else:
            total = 0

        if system.analysis_db.exists():
            with open(system.analysis_db, 'r', encoding='utf-8') as f:
                analyzed = json.load(f)
            analyzed_count = len(analyzed)
        else:
            analyzed_count = 0

        print("\n📊 分析ステータス")
        print("="*50)
        print(f"総論文数: {total:,}件")
        print(f"分析済み: {analyzed_count:,}件")
        print(f"未分析: {total - analyzed_count:,}件")

        if total > 0:
            progress = (analyzed_count / total) * 100
            print(f"進捗: {progress:.1f}%")


if __name__ == "__main__":
    main()