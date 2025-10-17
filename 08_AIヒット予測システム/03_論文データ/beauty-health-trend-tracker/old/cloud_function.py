"""
Google Cloud Functions用の実装
より軽量で安価な実行方法
"""

import functions_framework
import json
import os
from datetime import datetime
from typing import Dict, Any

# 簡易版のコレクターとサマライザーをインポート
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
from google.cloud import storage

# Gemini設定
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

# GCS設定
BUCKET_NAME = os.environ.get('GCS_BUCKET_NAME', '')

@functions_framework.http
def collect_trends(request):
    """
    HTTP Cloud Function エントリーポイント
    
    Args:
        request: Flask Request object
    Returns:
        Flask Response object
    """
    
    # CORSヘッダー
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    # OPTIONS リクエストの処理（CORS）
    if request.method == 'OPTIONS':
        headers['Access-Control-Allow-Methods'] = 'POST'
        headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return ('', 204, headers)
    
    try:
        # リクエストパラメータ取得
        request_json = request.get_json(silent=True) or {}
        days_back = request_json.get('days_back', 7)  # デフォルト1週間
        keywords = request_json.get('keywords', ['NMN', 'collagen', 'CBD'])
        max_papers = request_json.get('max_papers', 3)  # 関数の制限時間を考慮
        
        # 1. PubMed検索
        papers_data = search_pubmed(keywords[:3], max_papers, days_back)
        
        # 2. AI要約（Gemini使用可能な場合）
        if GEMINI_API_KEY and papers_data:
            analysis = analyze_papers(papers_data)
        else:
            analysis = {
                'status': 'collected_only',
                'message': 'Papers collected but no analysis (missing Gemini key)',
                'papers_count': sum(len(p) for p in papers_data.values())
            }
        
        # 3. GCSに保存（設定されている場合）
        if BUCKET_NAME:
            save_to_gcs(papers_data, analysis)
        
        # レスポンス
        response = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'papers_collected': sum(len(p) for p in papers_data.values()),
            'keywords_analyzed': len(papers_data),
            'analysis': analysis
        }
        
        return (json.dumps(response, ensure_ascii=False), 200, headers)
        
    except Exception as e:
        error_response = {
            'success': False,
            'error': str(e)
        }
        return (json.dumps(error_response), 500, headers)


def search_pubmed(keywords: list, max_results: int, days_back: int) -> Dict[str, list]:
    """
    PubMedから論文を検索（簡易版）
    
    Args:
        keywords: 検索キーワードリスト
        max_results: キーワードあたりの最大取得件数
        days_back: 何日前までを検索するか
    
    Returns:
        キーワードごとの論文データ
    """
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    results = {}
    
    for keyword in keywords:
        try:
            # 検索
            search_params = {
                'db': 'pubmed',
                'term': keyword,
                'retmax': max_results,
                'retmode': 'xml',
                'sort': 'relevance'
            }
            
            search_response = requests.get(
                f"{base_url}esearch.fcgi",
                params=search_params,
                timeout=10
            )
            
            # PMIDを抽出
            root = ET.fromstring(search_response.text)
            pmids = [id_elem.text for id_elem in root.findall('.//Id')]
            
            if pmids:
                # 詳細取得
                fetch_params = {
                    'db': 'pubmed',
                    'id': ','.join(pmids),
                    'retmode': 'xml',
                    'rettype': 'abstract'
                }
                
                fetch_response = requests.get(
                    f"{base_url}efetch.fcgi",
                    params=fetch_params,
                    timeout=10
                )
                
                # 論文データをパース
                papers = parse_papers(fetch_response.text)
                results[keyword] = papers
            else:
                results[keyword] = []
                
        except Exception as e:
            print(f"Error searching {keyword}: {e}")
            results[keyword] = []
    
    return results


def parse_papers(xml_text: str) -> list:
    """XMLから論文情報を抽出（簡易版）"""
    papers = []
    try:
        root = ET.fromstring(xml_text)
        for article in root.findall('.//PubmedArticle'):
            paper = {}
            
            # PMID
            pmid_elem = article.find('.//PMID')
            if pmid_elem is not None:
                paper['pmid'] = pmid_elem.text
            
            # タイトル
            title_elem = article.find('.//ArticleTitle')
            if title_elem is not None:
                paper['title'] = title_elem.text
            
            # 要約
            abstract_elem = article.find('.//Abstract/AbstractText')
            if abstract_elem is not None:
                paper['abstract'] = abstract_elem.text
            
            papers.append(paper)
            
    except Exception as e:
        print(f"Parse error: {e}")
    
    return papers


def analyze_papers(papers_data: Dict) -> Dict:
    """論文をAIで分析（簡易版）"""
    if not model:
        return {'error': 'Gemini model not initialized'}
    
    all_titles = []
    all_abstracts = []
    
    for keyword, papers in papers_data.items():
        for paper in papers:
            all_titles.append(paper.get('title', ''))
            all_abstracts.append(paper.get('abstract', '')[:500])  # 文字数制限
    
    # 簡易的なプロンプト
    prompt = f"""
以下の論文タイトルと要旨から、美容・健康分野のトレンドを分析してください。

タイトル:
{chr(10).join(all_titles[:5])}

JSON形式で以下を返してください:
{{
    "top_trends": ["トレンド1", "トレンド2", "トレンド3"],
    "key_ingredients": ["成分1", "成分2", "成分3"],
    "insights": "50文字以内の総括"
}}
"""
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # JSONを抽出
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        
        return json.loads(text.strip())
        
    except Exception as e:
        return {
            'error': str(e),
            'top_trends': [],
            'key_ingredients': [],
            'insights': 'Analysis failed'
        }


def save_to_gcs(papers_data: Dict, analysis: Dict):
    """Google Cloud Storageに保存"""
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 結果を保存
        blob = bucket.blob(f'functions/analysis_{timestamp}.json')
        data = {
            'timestamp': timestamp,
            'papers': papers_data,
            'analysis': analysis
        }
        blob.upload_from_string(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type='application/json'
        )
        
        # 最新版も保存
        latest_blob = bucket.blob('functions/latest.json')
        latest_blob.upload_from_string(
            json.dumps(data, ensure_ascii=False, indent=2),
            content_type='application/json'
        )
        
    except Exception as e:
        print(f"GCS save error: {e}")


@functions_framework.http
def get_latest_analysis(request):
    """最新の分析結果を取得するエンドポイント"""
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
    }
    
    if not BUCKET_NAME:
        return (json.dumps({'error': 'GCS not configured'}), 404, headers)
    
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob('functions/latest.json')
        
        if blob.exists():
            content = blob.download_as_text()
            return (content, 200, headers)
        else:
            return (json.dumps({'error': 'No data found'}), 404, headers)
            
    except Exception as e:
        return (json.dumps({'error': str(e)}), 500, headers)
