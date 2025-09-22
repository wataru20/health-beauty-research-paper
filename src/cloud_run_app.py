#!/usr/bin/env python3
"""
Cloud Run用アプリケーション
HTTPエンドポイントとして論文収集・分析機能を提供
"""

import os
import json
import logging
from flask import Flask, request, jsonify, send_from_directory
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
sys.path.append('/app')

from src.collectors.pubmed_collector import PubMedCollector
from src.analyzers.paper_summarizer import PaperSummarizer
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flaskアプリ初期化
app = Flask(__name__)

# Google Cloud Storageの設定（オプション）
USE_GCS = os.environ.get('USE_GCS', 'false').lower() == 'true'
GCS_BUCKET = os.environ.get('GCS_BUCKET_NAME', '')

class CloudTrendTracker:
    """Cloud Run用トレンド追跡クラス"""
    
    def __init__(self):
        self.data_dir = Path('/tmp/data')  # Cloud Runの一時ストレージ
        self.data_dir.mkdir(exist_ok=True)
        (self.data_dir / 'raw').mkdir(exist_ok=True)
        (self.data_dir / 'processed').mkdir(exist_ok=True)
        (self.data_dir / 'trends').mkdir(exist_ok=True)
        
        # API キー
        self.ncbi_api_key = os.environ.get('NCBI_API_KEY')
        self.gemini_api_key = os.environ.get('GEMINI_API_KEY')
        
        # キーワード設定を読み込み
        with open('/app/configs/keywords.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
    
    def collect_and_analyze(self, days_back=30, max_papers=5):
        """論文収集と分析を実行"""
        try:
            # 1. 論文収集
            logger.info("Starting paper collection...")
            collector = PubMedCollector(api_key=self.ncbi_api_key)
            
            # サンプルキーワード（無料枠を考慮）
            keywords = [
                "NMN anti-aging skin",
                "collagen supplement",
                "hyaluronic acid hydration",
                "CBD skincare",
                "retinol anti-aging"
            ]
            
            results = collector.collect_papers_for_keywords(
                keywords[:3],  # 最初の3つのみ（無料枠考慮）
                max_per_keyword=max_papers,
                days_back=days_back
            )
            
            # 2. 論文要約・分析
            logger.info("Starting analysis...")
            if self.gemini_api_key:
                summarizer = PaperSummarizer(api_key=self.gemini_api_key)
                
                # 要約
                summarized_data = {}
                for keyword, papers in results.items():
                    if papers:
                        summarized = summarizer.batch_summarize(papers[:2], max_papers=2)
                        summarized_data[keyword] = summarized
                
                # トレンド分析
                analysis = summarizer.analyze_trends(summarized_data)
                
                # GCSに保存（オプション）
                if USE_GCS and GCS_BUCKET:
                    self._save_to_gcs(summarized_data, analysis)
                
                return {
                    'status': 'success',
                    'papers_collected': sum(len(p) for p in results.values()),
                    'keywords_analyzed': len(results),
                    'analysis': analysis
                }
            else:
                return {
                    'status': 'partial',
                    'message': 'Papers collected but no Gemini API key for analysis',
                    'papers_collected': sum(len(p) for p in results.values())
                }
                
        except Exception as e:
            logger.error(f"Error in collect_and_analyze: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _save_to_gcs(self, papers_data, analysis):
        """Google Cloud Storageに結果を保存"""
        try:
            from google.cloud import storage
            
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 論文データを保存
            papers_blob = bucket.blob(f'data/papers_{timestamp}.json')
            papers_blob.upload_from_string(
                json.dumps(papers_data, ensure_ascii=False, indent=2),
                content_type='application/json'
            )
            
            # 分析結果を保存
            analysis_blob = bucket.blob(f'data/analysis_{timestamp}.json')
            analysis_blob.upload_from_string(
                json.dumps(analysis, ensure_ascii=False, indent=2),
                content_type='application/json'
            )
            
            # 最新版として保存
            latest_blob = bucket.blob('data/latest_analysis.json')
            latest_blob.upload_from_string(
                json.dumps(analysis, ensure_ascii=False, indent=2),
                content_type='application/json'
            )
            
            logger.info(f"Data saved to GCS: {GCS_BUCKET}")
            
        except Exception as e:
            logger.error(f"GCS save error: {str(e)}")

# グローバルインスタンス
tracker = CloudTrendTracker()

@app.route('/')
def index():
    """ヘルスチェック用エンドポイント"""
    return jsonify({
        'service': 'Beauty & Health Trend Tracker',
        'status': 'healthy',
        'endpoints': {
            '/collect': 'POST - Collect and analyze papers',
            '/trigger': 'POST - Cloud Scheduler trigger endpoint',
            '/dashboard': 'GET - View dashboard'
        }
    })

@app.route('/collect', methods=['POST'])
def collect():
    """論文収集・分析エンドポイント"""
    data = request.get_json() or {}
    
    days_back = data.get('days_back', 30)
    max_papers = data.get('max_papers', 5)
    
    result = tracker.collect_and_analyze(days_back, max_papers)
    
    return jsonify(result)

@app.route('/trigger', methods=['POST'])
def trigger():
    """Cloud Scheduler用トリガーエンドポイント"""
    # Cloud Schedulerからのリクエストを検証
    auth_header = request.headers.get('Authorization')
    
    # 簡易的な認証（本番環境では適切な認証を実装）
    expected_token = os.environ.get('SCHEDULER_TOKEN', '')
    if expected_token and auth_header != f'Bearer {expected_token}':
        return jsonify({'error': 'Unauthorized'}), 401
    
    # デフォルト設定で実行
    result = tracker.collect_and_analyze(days_back=30, max_papers=5)
    
    logger.info(f"Scheduled job completed: {result}")
    
    return jsonify(result)

@app.route('/dashboard')
def dashboard():
    """ダッシュボード表示"""
    return send_from_directory('/app/dashboard', 'index.html')

@app.route('/dashboard/<path:path>')
def dashboard_static(path):
    """ダッシュボードの静的ファイル"""
    return send_from_directory('/app/dashboard', path)

@app.route('/data/<path:filename>')
def serve_data(filename):
    """データファイルを提供"""
    if USE_GCS and GCS_BUCKET:
        # GCSから取得
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(GCS_BUCKET)
            blob = bucket.blob(f'data/{filename}')
            content = blob.download_as_text()
            return content, 200, {'Content-Type': 'application/json'}
        except Exception as e:
            return jsonify({'error': str(e)}), 404
    else:
        # ローカルファイルから取得
        file_path = Path('/tmp/data') / filename
        if file_path.exists():
            return send_from_directory('/tmp/data', filename)
        else:
            return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    # Cloud Runのポート設定
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
