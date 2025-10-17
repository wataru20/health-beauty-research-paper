#!/usr/bin/env python3
"""
ローカル環境用メインスクリプト
環境変数対応・定期実行機能付き
"""

import os
import sys
import json
import time
import schedule
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from src.collectors.pubmed_collector import PubMedCollector
from src.analyzers.paper_summarizer import PaperSummarizer

# 環境変数を読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/tracker.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class LocalTrendTracker:
    """ローカル環境用トレンド追跡クラス"""
    
    def __init__(self):
        """初期化"""
        self.project_root = Path(__file__).parent.parent
        self.config_path = self.project_root / "configs" / "keywords.json"
        
        # 環境変数から設定を読み込み
        self.data_dir = Path(os.getenv('DATA_DIR', './data'))
        self.backup_dir = Path(os.getenv('BACKUP_DIR', './backups'))
        
        # ディレクトリ作成
        (self.data_dir / "raw").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "processed").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "trends").mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # ログディレクトリ
        Path("logs").mkdir(exist_ok=True)
        
        # キーワード設定を読み込み
        self.config = self._load_config()
        
        # API キー取得
        self.ncbi_api_key = os.getenv('NCBI_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        
        if not self.gemini_api_key:
            logger.warning("⚠️ Gemini APIキーが設定されていません。.envファイルを確認してください。")
        
        # デフォルト設定
        self.days_back = int(os.getenv('DAYS_BACK', 30))
        self.max_papers = int(os.getenv('MAX_PAPERS_PER_KEYWORD', 5))
    
    def _load_config(self) -> dict:
        """キーワード設定を読み込み"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"設定ファイルが見つかりません: {self.config_path}")
            return {}
    
    def _get_priority_keywords(self) -> list:
        """優先キーワードを取得"""
        # ハードコードされた優先キーワード（英語）
        priority_keywords_en = [
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
        
        # 設定ファイルから日本語キーワードも取得
        priority_keywords_jp = []
        if self.config:
            # 新興成分を優先
            if 'ingredients' in self.config and 'emerging' in self.config['ingredients']:
                priority_keywords_jp.extend(self.config['ingredients']['emerging'].get('keywords', [])[:5])
        
        return priority_keywords_en[:5]  # 無料枠を考慮して5個まで
    
    def collect_papers(self):
        """論文を収集"""
        logger.info("=" * 50)
        logger.info("📚 論文収集を開始します")
        logger.info(f"期間: 過去{self.days_back}日間")
        logger.info(f"キーワードあたり最大: {self.max_papers}件")
        
        # コレクター初期化
        collector = PubMedCollector(api_key=self.ncbi_api_key)
        
        # キーワード取得
        keywords = self._get_priority_keywords()
        logger.info(f"検索キーワード: {keywords}")
        
        # 論文収集
        results = collector.collect_papers_for_keywords(
            keywords,
            max_per_keyword=self.max_papers,
            days_back=self.days_back
        )
        
        # 結果を保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = self.data_dir / "raw" / f"papers_{timestamp}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        total_papers = sum(len(papers) for papers in results.values())
        logger.info(f"✅ 収集完了: {total_papers}件の論文")
        logger.info(f"保存先: {output_path}")
        
        return output_path
    
    def analyze_papers(self):
        """論文を分析・要約"""
        logger.info("=" * 50)
        logger.info("🔬 論文分析を開始します")
        
        if not self.gemini_api_key:
            logger.error("❌ Gemini APIキーが設定されていません")
            return None
        
        # 最新の生データを取得
        raw_files = sorted(
            (self.data_dir / "raw").glob("papers_*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        if not raw_files:
            logger.error("❌ 分析する論文データが見つかりません")
            return None
        
        latest_file = raw_files[0]
        logger.info(f"分析対象: {latest_file.name}")
        
        # データ読み込み
        with open(latest_file, 'r', encoding='utf-8') as f:
            papers_data = json.load(f)
        
        # 要約器初期化
        summarizer = PaperSummarizer(api_key=self.gemini_api_key)
        
        # 各キーワードの論文を要約
        summarized_data = {}
        
        for keyword, papers in papers_data.items():
            if papers:
                logger.info(f"要約中: {keyword}")
                summarized = summarizer.batch_summarize(papers, max_papers=3)
                summarized_data[keyword] = summarized
        
        # 処理済みデータを保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        processed_path = self.data_dir / "processed" / f"summarized_{timestamp}.json"
        
        with open(processed_path, 'w', encoding='utf-8') as f:
            json.dump(summarized_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 要約完了: {processed_path}")
        
        # トレンド分析
        logger.info("📊 トレンド分析中...")
        trend_analysis = summarizer.analyze_trends(summarized_data)
        
        # 分析結果を保存
        analysis_path = self.data_dir / "trends" / f"analysis_{timestamp}.json"
        with open(analysis_path, 'w', encoding='utf-8') as f:
            json.dump(trend_analysis, f, ensure_ascii=False, indent=2)
        
        # 最新版としても保存（ダッシュボード用）
        latest_analysis = self.data_dir / "trends" / "latest_analysis.json"
        latest_papers = self.data_dir / "processed" / "latest_papers.json"
        
        with open(latest_analysis, 'w', encoding='utf-8') as f:
            json.dump(trend_analysis, f, ensure_ascii=False, indent=2)
        
        with open(latest_papers, 'w', encoding='utf-8') as f:
            json.dump(summarized_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 分析完了: {analysis_path}")
        
        # インサイト表示
        logger.info("\n💡 トレンドインサイト:")
        for insight in trend_analysis.get('trend_insights', []):
            logger.info(f"  • {insight}")
        
        return analysis_path
    
    def backup_data(self):
        """データをバックアップ"""
        logger.info("💾 データバックアップを実行中...")
        
        timestamp = datetime.now().strftime('%Y%m%d')
        backup_path = self.backup_dir / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        # データディレクトリをコピー
        import shutil
        for subdir in ['raw', 'processed', 'trends']:
            src = self.data_dir / subdir
            dst = backup_path / subdir
            if src.exists():
                shutil.copytree(src, dst, dirs_exist_ok=True)
        
        logger.info(f"✅ バックアップ完了: {backup_path}")
    
    def run_full_cycle(self):
        """フルサイクル実行"""
        logger.info("\n" + "=" * 50)
        logger.info("🚀 フルサイクル実行開始")
        logger.info(f"実行時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        try:
            # 1. 論文収集
            self.collect_papers()
            
            # 2. 分析・要約
            self.analyze_papers()
            
            # 3. バックアップ（週1回）
            if datetime.now().weekday() == 0:  # 月曜日
                self.backup_data()
            
            logger.info("✅ フルサイクル完了")
            
        except Exception as e:
            logger.error(f"❌ エラーが発生しました: {e}")
            raise
    
    def schedule_jobs(self, schedule_type='weekly'):
        """定期実行をスケジュール"""
        if schedule_type == 'weekly':
            # 毎週月曜日 9:00
            schedule.every().monday.at("09:00").do(self.run_full_cycle)
            logger.info("📅 毎週月曜日 9:00 に実行するよう設定しました")
        
        elif schedule_type == 'daily':
            # 毎日 9:00
            schedule.every().day.at("09:00").do(self.run_full_cycle)
            logger.info("📅 毎日 9:00 に実行するよう設定しました")
        
        elif schedule_type == 'hourly':
            # 毎時（テスト用）
            schedule.every().hour.do(self.run_full_cycle)
            logger.info("📅 毎時実行するよう設定しました")
    
    def run_scheduler(self):
        """スケジューラーを実行"""
        logger.info("⏰ スケジューラーを開始しました")
        logger.info("Ctrl+C で終了します")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1分ごとにチェック
            except KeyboardInterrupt:
                logger.info("\n👋 スケジューラーを終了します")
                break


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        description='美容・健康成分トレンド追跡システム（ローカル版）'
    )
    
    parser.add_argument(
        '--mode',
        choices=['collect', 'analyze', 'all', 'schedule'],
        default='all',
        help='実行モード'
    )
    
    parser.add_argument(
        '--schedule-type',
        choices=['weekly', 'daily', 'hourly'],
        default='weekly',
        help='スケジュール実行の頻度'
    )
    
    args = parser.parse_args()
    
    # トラッカー初期化
    tracker = LocalTrendTracker()
    
    if args.mode == 'collect':
        tracker.collect_papers()
    
    elif args.mode == 'analyze':
        tracker.analyze_papers()
    
    elif args.mode == 'all':
        tracker.run_full_cycle()
    
    elif args.mode == 'schedule':
        # 初回実行
        tracker.run_full_cycle()
        # スケジューラー開始
        tracker.schedule_jobs(args.schedule_type)
        tracker.run_scheduler()


if __name__ == "__main__":
    main()
