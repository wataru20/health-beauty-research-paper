"""
PubMed論文収集モジュール
NCBI E-utilities APIを使用して論文データを自動収集
"""

import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
import time
import json
from datetime import datetime, timedelta
import hashlib
from pathlib import Path


class PubMedCollector:
    """PubMed論文収集クラス"""
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初期化
        
        Args:
            api_key: NCBI API キー（オプション。設定すると制限が緩和される）
        """
        self.api_key = api_key
        self.rate_limit = 10 if api_key else 3  # API keyありで10req/s、なしで3req/s
        self.last_request_time = 0
        
    def _wait_for_rate_limit(self):
        """レート制限を守るための待機処理"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last_request < min_interval:
            time.sleep(min_interval - time_since_last_request)
        
        self.last_request_time = time.time()
    
    def search_papers(self, query: str, max_results: int = 10, 
                     days_back: int = 30) -> List[str]:
        """
        論文を検索してPMIDリストを取得
        
        Args:
            query: 検索クエリ
            max_results: 最大取得件数
            days_back: 何日前までの論文を検索するか
        
        Returns:
            PMIDのリスト
        """
        self._wait_for_rate_limit()
        
        # 日付範囲の設定
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'xml',
            'datetype': 'pdat',
            'mindate': start_date.strftime('%Y/%m/%d'),
            'maxdate': end_date.strftime('%Y/%m/%d'),
            'sort': 'relevance'
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            response = requests.get(
                f"{self.BASE_URL}esearch.fcgi",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            # XMLパース
            root = ET.fromstring(response.text)
            pmids = [id_elem.text for id_elem in root.findall('.//Id')]
            
            return pmids
            
        except Exception as e:
            print(f"検索エラー ({query}): {e}")
            return []
    
    def fetch_paper_details(self, pmids: List[str]) -> List[Dict]:
        """
        PMIDリストから論文の詳細情報を取得
        
        Args:
            pmids: PMIDのリスト
        
        Returns:
            論文情報の辞書リスト
        """
        if not pmids:
            return []
        
        self._wait_for_rate_limit()
        
        params = {
            'db': 'pubmed',
            'id': ','.join(pmids),
            'retmode': 'xml',
            'rettype': 'abstract'
        }
        
        if self.api_key:
            params['api_key'] = self.api_key
        
        try:
            response = requests.get(
                f"{self.BASE_URL}efetch.fcgi",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            # XMLパース
            root = ET.fromstring(response.text)
            papers = []
            
            for article in root.findall('.//PubmedArticle'):
                paper_data = self._parse_article(article)
                if paper_data:
                    papers.append(paper_data)
            
            return papers
            
        except Exception as e:
            print(f"詳細取得エラー: {e}")
            return []
    
    def _parse_article(self, article_elem) -> Optional[Dict]:
        """
        XML要素から論文情報を抽出
        
        Args:
            article_elem: XML要素
        
        Returns:
            論文情報の辞書
        """
        try:
            medline = article_elem.find('.//MedlineCitation')
            article = medline.find('.//Article')
            
            # PMID
            pmid = medline.find('.//PMID').text
            
            # タイトル
            title_elem = article.find('.//ArticleTitle')
            title = title_elem.text if title_elem is not None else "No title"
            
            # 要約
            abstract_elem = article.find('.//Abstract/AbstractText')
            abstract = abstract_elem.text if abstract_elem is not None else ""
            
            # 著者リスト
            authors = []
            author_list = article.find('.//AuthorList')
            if author_list is not None:
                for author in author_list.findall('.//Author'):
                    last_name = author.find('.//LastName')
                    fore_name = author.find('.//ForeName')
                    if last_name is not None:
                        name = last_name.text
                        if fore_name is not None:
                            name = f"{fore_name.text} {name}"
                        authors.append(name)
            
            # 出版日
            pub_date = article.find('.//Journal/JournalIssue/PubDate')
            date_str = "Unknown"
            if pub_date is not None:
                year = pub_date.find('.//Year')
                month = pub_date.find('.//Month')
                day = pub_date.find('.//Day')
                
                if year is not None:
                    date_str = year.text
                    if month is not None:
                        date_str = f"{date_str}-{month.text}"
                        if day is not None:
                            date_str = f"{date_str}-{day.text}"
            
            # ジャーナル名
            journal_elem = article.find('.//Journal/Title')
            journal = journal_elem.text if journal_elem is not None else "Unknown"
            
            # キーワード
            keywords = []
            keyword_list = medline.find('.//KeywordList')
            if keyword_list is not None:
                for keyword in keyword_list.findall('.//Keyword'):
                    keywords.append(keyword.text)
            
            # MeSH Terms
            mesh_terms = []
            mesh_list = medline.find('.//MeshHeadingList')
            if mesh_list is not None:
                for mesh in mesh_list.findall('.//MeshHeading/DescriptorName'):
                    mesh_terms.append(mesh.text)
            
            # ユニークIDの生成（重複チェック用）
            unique_id = hashlib.md5(f"{pmid}".encode()).hexdigest()
            
            return {
                'pmid': pmid,
                'unique_id': unique_id,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'publication_date': date_str,
                'journal': journal,
                'keywords': keywords,
                'mesh_terms': mesh_terms,
                'url': f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                'collected_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"論文パースエラー: {e}")
            return None
    
    def collect_papers_for_keywords(self, keywords: List[str], 
                                   max_per_keyword: int = 10,
                                   days_back: int = 30) -> Dict[str, List[Dict]]:
        """
        複数のキーワードで論文を収集
        
        Args:
            keywords: キーワードリスト
            max_per_keyword: キーワードあたりの最大取得件数
            days_back: 何日前までの論文を検索するか
        
        Returns:
            キーワードごとの論文リスト
        """
        results = {}
        total_keywords = len(keywords)
        
        for idx, keyword in enumerate(keywords, 1):
            print(f"収集中 [{idx}/{total_keywords}]: {keyword}")
            
            # 検索
            pmids = self.search_papers(keyword, max_per_keyword, days_back)
            
            # 詳細取得
            if pmids:
                papers = self.fetch_paper_details(pmids)
                results[keyword] = papers
                print(f"  → {len(papers)}件取得")
            else:
                results[keyword] = []
                print(f"  → 0件")
        
        return results
    
    def save_results(self, results: Dict, output_dir: Path):
        """
        結果をJSON形式で保存
        
        Args:
            results: 収集結果
            output_dir: 出力ディレクトリ
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # タイムスタンプ付きファイル名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = output_dir / f"papers_{timestamp}.json"
        
        # 保存
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"結果を保存しました: {filename}")
        return filename


# テスト実行用
if __name__ == "__main__":
    # コレクター初期化
    collector = PubMedCollector()
    
    # サンプルキーワードで検索
    test_keywords = ["NMN skin", "collagen supplement", "hyaluronic acid"]
    results = collector.collect_papers_for_keywords(
        test_keywords,
        max_per_keyword=5,
        days_back=30
    )
    
    # 結果表示
    for keyword, papers in results.items():
        print(f"\n=== {keyword} ===")
        for paper in papers[:2]:  # 最初の2件のみ表示
            print(f"- {paper['title'][:100]}...")
            print(f"  Authors: {', '.join(paper['authors'][:3])}")
            print(f"  Date: {paper['publication_date']}")
