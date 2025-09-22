#!/usr/bin/env python3
"""
美容・健康成分トレンド追跡システム - メインスクリプト
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
import shutil

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.collectors.pubmed_collector import PubMedCollector
from src.analyzers.paper_summarizer import PaperSummarizer


class TrendTracker:
    """トレンド追跡システムのメインクラス"""
    
    def __init__(self):
        """初期化"""
        self.project_root = Path(__file__).parent.parent
        self.config_path = self.project_root / "configs" / "keywords.json"
        self.data_dir = self.project_root / "data"
        
        # ディレクトリ作成
        (self.data_dir / "raw").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "processed").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "trends").mkdir(parents=True, exist_ok=True)
        
        # 設定読み込み
        self.config = self._load_config()
        
        # API キー取得
        self.ncbi_api_key = os.environ.get('NCBI_API_KEY')
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
    
    def _load_config(self) -> dict:
        """キーワード設定を読み込み"""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _get_all_keywords(self) -> list:
        """全キーワードをリスト形式で取得"""
        keywords = []
        
        # ニーズ・悩み軸のキーワード
        for category in self.config['categories'].values():
            for subcategory in category['subcategories'].values():
                keywords.extend(subcategory['keywords'])
        
        # 成分軸のキーワード  
        for ingredient_group in self.config['ingredients'].values():
            if isinstance(ingredient_group, dict) and 'subcategories' in ingredient_group:
                for subcategory in ingredient_group['subcategories'].values():
                    keywords.extend(subcategory['keywords'])
            elif isinstance(ingredient_group, dict) and 'keywords' in ingredient_group:
                keywords.extend(ingredient_group['keywords'])
        
        # コンセプト軸のキーワード
        for concept_group in self.config['concepts'].values():
            if 'keywords' in concept_group:
                keywords.extend(concept_group['keywords'])
        
        return list(set(keywords))  # 重複除去
    
    def collect_papers(self, days_back: int = 30, max_papers: int = 10):
        """
        論文を収集
        
        Args:
            days_back: 何日前までの論文を検索するか
            max_papers: キーワードあたりの最大取得件数
        """
        print("=" * 50)
        print("📚 論文収集を開始します")
        print("=" * 50)
        
        # コレクター初期化
        collector = PubMedCollector(api_key=self.ncbi_api_key)
        
        # キーワード取得（サンプリング）
        all_keywords = self._get_all_keywords()
        
        # 優先キーワードを設定（重要な成分を優先）
        priority_keywords = [
            "NMN", "collagen", "hyaluronic acid", "retinol", "CBD",
            "exosome", "stem cell", "peptide", "ceramide", "niacinamide"
        ]
        
        # 英語キーワードに変換（簡易マッピング）
        keyword_mapping = {
            "NMN": "NMN anti-aging",
            "コラーゲン": "collagen supplement skin",
            "ヒアルロン酸": "hyaluronic acid skin hydration",
            "レチノール": "retinol anti-aging skincare",
            "CBD": "CBD skincare inflammation",
            "エクソソーム": "exosome skin regeneration",
            "ヒト幹細胞": "stem cell cosmetics",
            "ペプチド": "peptide anti-aging skin",
            "セラミド": "ceramide skin barrier",
            "ナイアシンアミド": "niacinamide skin brightening"
        }
        
        # 検索キーワードを選択（優先キーワード + ランダムサンプル）
        search_keywords = priority_keywords[:5]  # 無料枠を考慮して制限
        
        print(f"検索キーワード数: {len(search_keywords)}")
        print(f"期間: 過去{days_back}日間")
        print(f"キーワードあたり最大: {max_papers}件\n")
        
        # 論文収集
        results = collector.collect_papers_for_keywords(
            search_keywords,
            max_per_keyword=max_papers,
            days_back=days_back
        )
        
        # 結果を保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = self.data_dir / "raw" / f"papers_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 収集完了: {output_path}")
        
        # 統計表示
        total_papers = sum(len(papers) for papers in results.values())
        print(f"総論文数: {total_papers}件")
        
        return output_path
    
    def analyze_papers(self):
        """論文を分析・要約"""
        print("=" * 50)
        print("🔬 論文分析を開始します")
        print("=" * 50)
        
        if not self.gemini_api_key:
            print("⚠️ Gemini APIキーが設定されていません")
            print("環境変数 GEMINI_API_KEY を設定してください")
            return None
        
        # 最新の生データを取得
        raw_files = sorted(
            (self.data_dir / "raw").glob("papers_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not raw_files:
            print("❌ 分析する論文データが見つかりません")
            return None
        
        latest_file = raw_files[0]
        print(f"分析対象: {latest_file.name}")
        
        # データ読み込み
        with open(latest_file, 'r', encoding='utf-8') as f:
            papers_data = json.load(f)
        
        # 要約器初期化
        summarizer = PaperSummarizer(api_key=self.gemini_api_key)
        
        # 各キーワードの論文を要約
        summarized_data = {}
        total_papers = 0
        
        for keyword, papers in papers_data.items():
            if papers:
                print(f"\n要約中: {keyword}")
                # 無料枠を考慮して最大3件まで
                summarized = summarizer.batch_summarize(papers, max_papers=3)
                summarized_data[keyword] = summarized
                total_papers += len(summarized)
        
        # 処理済みデータを保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        processed_path = self.data_dir / "processed" / f"summarized_{timestamp}.json"
        
        with open(processed_path, 'w', encoding='utf-8') as f:
            json.dump(summarized_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 要約完了: {processed_path}")
        
        # トレンド分析
        print("\n📊 トレンド分析中...")
        trend_analysis = summarizer.analyze_trends(summarized_data)
        
        # 分析結果を保存
        analysis_path = self.data_dir / "trends" / f"analysis_{timestamp}.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(trend_analysis, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 分析完了: {analysis_path}")
        
        # インサイト表示
        print("\n💡 トレンドインサイト:")
        for insight in trend_analysis.get('trend_insights', []):
            print(f"  • {insight}")
        
        return analysis_path
    
    def prepare_dashboard_data(self):
        """ダッシュボード用のデータを準備"""
        print("=" * 50)
        print("📊 ダッシュボードデータを準備します")
        print("=" * 50)
        
        # 最新の分析結果を取得
        trend_files = sorted(
            (self.data_dir / "trends").glob("analysis_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        processed_files = sorted(
            (self.data_dir / "processed").glob("summarized_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not trend_files or not processed_files:
            print("❌ 必要なデータファイルが見つかりません")
            return False
        
        # 最新ファイルをコピー
        latest_analysis = trend_files[0]
        latest_papers = processed_files[0]
        
        # ダッシュボード用のファイル名でコピー
        shutil.copy(
            latest_analysis,
            self.data_dir / "trends" / "latest_analysis.json"
        )
        
        shutil.copy(
            latest_papers,
            self.data_dir / "processed" / "latest_papers.json"
        )
        
        print("✅ ダッシュボードデータの準備完了")
        print(f"  分析: {latest_analysis.name}")
        print(f"  論文: {latest_papers.name}")
        
        return True
    
    def run(self, mode: str, **kwargs):
        """
        メイン実行
        
        Args:
            mode: 実行モード（collect, analyze, dashboard, all）
        """
        if mode in ['collect', 'all']:
            self.collect_papers(
                days_back=kwargs.get('days_back', 30),
                max_papers=kwargs.get('max_papers', 10)
            )
        
        if mode in ['analyze', 'all']:
            self.analyze_papers()
        
        if mode in ['dashboard', 'all']:
            self.prepare_dashboard_data()


def main():
    """エントリーポイント"""
    parser = argparse.ArgumentParser(
        description='美容・健康成分トレンド追跡システム'
    )
    
    parser.add_argument(
        '--mode',
        choices=['collect', 'analyze', 'dashboard', 'all'],
        default='all',
        help='実行モード'
    )
    
    parser.add_argument(
        '--days-back',
        type=int,
        default=30,
        help='何日前までの論文を検索するか'
    )
    
    parser.add_argument(
        '--max-papers',
        type=int,
        default=10,
        help='キーワードあたりの最大取得件数'
    )
    
    args = parser.parse_args()
    
    # システム実行
    tracker = TrendTracker()
    tracker.run(
        mode=args.mode,
        days_back=args.days_back,
        max_papers=args.max_papers
    )


if __name__ == "__main__":
    main()
