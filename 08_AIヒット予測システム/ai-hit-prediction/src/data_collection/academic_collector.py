"""
学術論文データ収集モジュール
Semantic Scholar APIを使用して論文データを収集
"""

import requests
import json
import os
from datetime import datetime
import time
from typing import List, Dict, Optional
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AcademicPaperCollector:
    """学術論文データを収集するクラス"""
    
    def __init__(self, data_dir: str = "data/raw"):
        """
        初期化
        
        Args:
            data_dir: データ保存先ディレクトリ
        """
        self.base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
        self.data_dir = data_dir
        self._ensure_data_dir()
        
    def _ensure_data_dir(self):
        """データディレクトリが存在することを確認"""
        os.makedirs(self.data_dir, exist_ok=True)
        logger.info(f"Data directory ensured: {self.data_dir}")
    
    def search_papers(self, query: str, limit: int = 10, offset: int = 0) -> Optional[Dict]:
        """
        論文を検索して基本情報を取得
        
        Args:
            query: 検索クエリ
            limit: 取得件数（最大100）
            offset: オフセット
            
        Returns:
            論文データの辞書、エラーの場合はNone
        """
        params = {
            'query': query,
            'limit': min(limit, 100),  # 最大100件
            'offset': offset,
            'fields': 'paperId,title,abstract,year,citationCount,authors,venue,publicationDate'
        }
        
        try:
            logger.info(f"Searching papers with query: '{query}'")
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Found {data.get('total', 0)} papers, retrieved {len(data.get('data', []))} papers")
                return data
            else:
                logger.error(f"API request failed with status code: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def collect_papers_for_keywords(self, keywords: List[str], papers_per_keyword: int = 10) -> Dict[str, List]:
        """
        複数のキーワードで論文を収集
        
        Args:
            keywords: 検索キーワードのリスト
            papers_per_keyword: 各キーワードで取得する論文数
            
        Returns:
            キーワードごとの論文データ
        """
        all_results = {}
        
        for keyword in keywords:
            logger.info(f"Collecting papers for keyword: {keyword}")
            papers = self.search_papers(keyword, limit=papers_per_keyword)
            
            if papers and 'data' in papers:
                all_results[keyword] = papers['data']
                # 処理済み論文データの要約を表示
                self._print_summary(keyword, papers['data'])
            else:
                all_results[keyword] = []
                logger.warning(f"No papers found for keyword: {keyword}")
            
            # API制限対策（1秒待機）
            time.sleep(1)
        
        return all_results
    
    def _print_summary(self, keyword: str, papers: List[Dict]):
        """論文データの要約を表示"""
        if papers:
            avg_citations = sum(p.get('citationCount', 0) or 0 for p in papers) / len(papers)
            recent_papers = sum(1 for p in papers if p.get('year', 0) and p['year'] >= 2020)
            logger.info(f"  - Average citations: {avg_citations:.1f}")
            logger.info(f"  - Recent papers (2020+): {recent_papers}/{len(papers)}")
    
    def save_to_file(self, data: Dict, prefix: str = "papers") -> str:
        """
        データをJSONファイルに保存
        
        Args:
            data: 保存するデータ
            prefix: ファイル名のプレフィックス
            
        Returns:
            保存したファイルパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.data_dir, f"{prefix}_{timestamp}.json")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Data saved to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            return ""
    
    def load_from_file(self, filepath: str) -> Optional[Dict]:
        """
        JSONファイルからデータを読み込み
        
        Args:
            filepath: 読み込むファイルパス
            
        Returns:
            読み込んだデータ、エラーの場合はNone
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Data loaded from: {filepath}")
            return data
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return None
    
    def extract_trend_metrics(self, papers: List[Dict]) -> Dict:
        """
        論文データからトレンドメトリクスを抽出
        
        Args:
            papers: 論文データのリスト
            
        Returns:
            トレンドメトリクス
        """
        if not papers:
            return {
                'total_papers': 0,
                'avg_citations': 0,
                'recent_papers_ratio': 0,
                'top_venues': []
            }
        
        # 基本統計
        total_papers = len(papers)
        total_citations = sum(p.get('citationCount', 0) or 0 for p in papers)
        avg_citations = total_citations / total_papers if total_papers > 0 else 0
        
        # 最近の論文の割合（2020年以降）
        recent_papers = sum(1 for p in papers if p.get('year', 0) and p['year'] >= 2020)
        recent_papers_ratio = recent_papers / total_papers if total_papers > 0 else 0
        
        # トップ会議・ジャーナル
        venues = {}
        for p in papers:
            venue = p.get('venue', 'Unknown')
            if venue:
                venues[venue] = venues.get(venue, 0) + 1
        
        top_venues = sorted(venues.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_papers': total_papers,
            'avg_citations': round(avg_citations, 2),
            'recent_papers_ratio': round(recent_papers_ratio, 2),
            'top_venues': top_venues
        }


def main():
    """メイン実行関数（テスト用）"""
    # コレクター初期化
    collector = AcademicPaperCollector()
    
    # 美容・スキンケア関連のキーワードリスト
    keywords = [
        "vitamin C skincare",
        "retinol anti-aging",
        "hyaluronic acid",
        "niacinamide skin",
        "peptides cosmetics"
    ]
    
    # データ収集
    logger.info("Starting academic paper collection...")
    results = collector.collect_papers_for_keywords(keywords, papers_per_keyword=5)
    
    # メトリクス抽出
    logger.info("\n=== Trend Metrics Summary ===")
    for keyword, papers in results.items():
        metrics = collector.extract_trend_metrics(papers)
        logger.info(f"\n{keyword}:")
        logger.info(f"  Total papers: {metrics['total_papers']}")
        logger.info(f"  Avg citations: {metrics['avg_citations']}")
        logger.info(f"  Recent papers ratio: {metrics['recent_papers_ratio']:.0%}")
        if metrics['top_venues']:
            logger.info(f"  Top venue: {metrics['top_venues'][0][0]} ({metrics['top_venues'][0][1]} papers)")
    
    # データ保存
    if results:
        filepath = collector.save_to_file(results, prefix="cosmetics_papers")
        logger.info(f"\nData collection completed. File saved: {filepath}")
    else:
        logger.warning("No data collected.")
    
    return results


if __name__ == "__main__":
    # テスト実行
    main()