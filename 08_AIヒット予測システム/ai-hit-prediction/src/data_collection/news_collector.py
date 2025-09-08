"""
ニュース記事データ収集モジュール
NewsAPIを使用して業界ニュースとトレンドを収集
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from functools import wraps
import requests
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def rate_limit(calls: int = 1, period: int = 1):
    """
    レート制限デコレーター
    
    Args:
        calls: 期間内の最大呼び出し回数
        period: 期間（秒）
    """
    min_interval = period / calls
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator


class NewsCollector:
    """ニュース記事を収集・分析するクラス"""
    
    def __init__(self, api_key: Optional[str] = None, data_dir: str = "data/raw"):
        """
        初期化
        
        Args:
            api_key: NewsAPI キー（Noneの場合は環境変数から取得）
            data_dir: データ保存先ディレクトリ
        """
        self.api_key = api_key or os.getenv('NEWS_API_KEY')
        self.base_url = "https://newsapi.org/v2"
        self.data_dir = data_dir
        self._ensure_data_dir()
        
        # NewsAPIクライアントの初期化（キーが利用可能な場合）
        self.newsapi_client = None
        if self.api_key and self.api_key != 'your_newsapi_key_here':
            try:
                from newsapi import NewsApiClient
                self.newsapi_client = NewsApiClient(api_key=self.api_key)
                logger.info("NewsAPI client initialized successfully")
            except ImportError:
                logger.warning("newsapi-python not installed. Using direct API calls.")
            except Exception as e:
                logger.error(f"Failed to initialize NewsAPI client: {e}")
        else:
            logger.warning("No valid NewsAPI key found. Using mock data mode.")
    
    def _ensure_data_dir(self):
        """データディレクトリが存在することを確認"""
        os.makedirs(self.data_dir, exist_ok=True)
        logger.info(f"Data directory ensured: {self.data_dir}")
    
    @rate_limit(calls=500, period=86400)  # NewsAPI: 500 calls/day for free tier
    def search_news(self, 
                   keywords: List[str], 
                   days_back: int = 7, 
                   language: str = 'en',
                   page_size: int = 100) -> Dict[str, Any]:
        """
        ニュース記事を検索
        
        Args:
            keywords: 検索キーワードのリスト
            days_back: 何日前までのニュースを取得するか
            language: 言語コード
            page_size: 取得する記事数
            
        Returns:
            検索結果の辞書
        """
        if not self.newsapi_client:
            logger.info("Using mock data for news search")
            return self._get_mock_news_data(keywords)
        
        from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        to_date = datetime.now().strftime('%Y-%m-%d')
        
        all_articles = []
        
        for keyword in keywords:
            try:
                logger.info(f"Searching news for keyword: '{keyword}'")
                
                # NewsAPI clientを使用
                response = self.newsapi_client.get_everything(
                    q=keyword,
                    from_param=from_date,
                    to=to_date,
                    language=language,
                    sort_by='popularity',
                    page_size=min(page_size, 100)  # Max 100 per request
                )
                
                if response['status'] == 'ok':
                    articles = response.get('articles', [])
                    logger.info(f"Found {len(articles)} articles for '{keyword}'")
                    
                    # キーワードを記事に追加
                    for article in articles:
                        article['search_keyword'] = keyword
                    
                    all_articles.extend(articles)
                else:
                    logger.error(f"API error for '{keyword}': {response.get('message', 'Unknown error')}")
                    
            except Exception as e:
                logger.error(f"Error searching news for '{keyword}': {e}")
        
        return {
            'status': 'ok',
            'totalResults': len(all_articles),
            'articles': all_articles,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_mock_news_data(self, keywords: List[str]) -> Dict[str, Any]:
        """
        モックニュースデータを生成（API不使用時のテスト用）
        
        Args:
            keywords: 検索キーワードのリスト
            
        Returns:
            モックデータの辞書
        """
        mock_articles = []
        
        for keyword in keywords:
            # キーワードごとに3つのモック記事を生成
            for i in range(3):
                mock_articles.append({
                    'source': {'id': None, 'name': f'Mock Source {i+1}'},
                    'author': f'Author {i+1}',
                    'title': f'Revolutionary {keyword} Product Launches in Beauty Industry',
                    'description': f'A new {keyword}-based product is taking the beauty world by storm...',
                    'url': f'https://example.com/article_{keyword}_{i}',
                    'urlToImage': None,
                    'publishedAt': (datetime.now() - timedelta(days=i)).isoformat(),
                    'content': f'Full article content about {keyword}...',
                    'search_keyword': keyword
                })
        
        return {
            'status': 'ok',
            'totalResults': len(mock_articles),
            'articles': mock_articles,
            'timestamp': datetime.now().isoformat(),
            'note': 'This is mock data for testing'
        }
    
    def extract_trends(self, articles: List[Dict]) -> Dict[str, Any]:
        """
        記事からトレンド情報を抽出
        
        Args:
            articles: 記事データのリスト
            
        Returns:
            トレンド情報の辞書
        """
        if not articles:
            return {
                'total_articles': 0,
                'keywords': {},
                'sources': {},
                'temporal_distribution': {}
            }
        
        trends = {
            'total_articles': len(articles),
            'keywords': {},
            'sources': {},
            'temporal_distribution': {},
            'top_articles': []
        }
        
        # キーワード別の記事数をカウント
        for article in articles:
            keyword = article.get('search_keyword', 'unknown')
            trends['keywords'][keyword] = trends['keywords'].get(keyword, 0) + 1
            
            # ソース別カウント
            source = article.get('source', {}).get('name', 'Unknown')
            trends['sources'][source] = trends['sources'].get(source, 0) + 1
            
            # 日付別分布
            published = article.get('publishedAt', '')
            if published:
                date = published[:10]  # YYYY-MM-DD format
                trends['temporal_distribution'][date] = \
                    trends['temporal_distribution'].get(date, 0) + 1
        
        # トップ記事を選出（最初の5記事）
        trends['top_articles'] = [
            {
                'title': a.get('title', ''),
                'source': a.get('source', {}).get('name', ''),
                'published': a.get('publishedAt', ''),
                'url': a.get('url', '')
            }
            for a in articles[:5]
        ]
        
        return trends
    
    def analyze_sentiment(self, articles: List[Dict]) -> Dict[str, float]:
        """
        記事のセンチメント分析（簡易版）
        
        Args:
            articles: 記事データのリスト
            
        Returns:
            センチメント分析結果
        """
        try:
            from textblob import TextBlob
        except ImportError:
            logger.warning("TextBlob not installed. Returning neutral sentiment.")
            return {'polarity': 0.0, 'subjectivity': 0.5}
        
        if not articles:
            return {'polarity': 0.0, 'subjectivity': 0.0}
        
        polarities = []
        subjectivities = []
        
        for article in articles:
            text = f"{article.get('title', '')} {article.get('description', '')}"
            if text.strip():
                try:
                    blob = TextBlob(text)
                    polarities.append(blob.sentiment.polarity)
                    subjectivities.append(blob.sentiment.subjectivity)
                except Exception as e:
                    logger.debug(f"Sentiment analysis error: {e}")
        
        return {
            'polarity': sum(polarities) / len(polarities) if polarities else 0.0,
            'subjectivity': sum(subjectivities) / len(subjectivities) if subjectivities else 0.0,
            'sentiment_label': self._get_sentiment_label(
                sum(polarities) / len(polarities) if polarities else 0.0
            )
        }
    
    def _get_sentiment_label(self, polarity: float) -> str:
        """センチメントスコアをラベルに変換"""
        if polarity > 0.1:
            return 'positive'
        elif polarity < -0.1:
            return 'negative'
        else:
            return 'neutral'
    
    def collect_industry_news(self, 
                             industry_keywords: List[str],
                             product_keywords: List[str],
                             days_back: int = 30) -> Dict[str, Any]:
        """
        業界ニュースを包括的に収集
        
        Args:
            industry_keywords: 業界関連キーワード
            product_keywords: 製品関連キーワード
            days_back: 取得期間
            
        Returns:
            収集したニュースと分析結果
        """
        logger.info("Starting comprehensive news collection...")
        
        # 複合キーワードを生成
        combined_keywords = []
        for industry in industry_keywords:
            for product in product_keywords:
                combined_keywords.append(f"{industry} {product}")
        
        # ニュース検索
        search_results = self.search_news(
            keywords=combined_keywords[:10],  # API制限を考慮
            days_back=days_back
        )
        
        articles = search_results.get('articles', [])
        
        # トレンド抽出
        trends = self.extract_trends(articles)
        
        # センチメント分析
        sentiment = self.analyze_sentiment(articles)
        
        # 結果をまとめる
        results = {
            'collection_date': datetime.now().isoformat(),
            'total_articles': len(articles),
            'trends': trends,
            'sentiment': sentiment,
            'articles': articles
        }
        
        # データ保存
        self.save_to_file(results, prefix="industry_news")
        
        return results
    
    def save_to_file(self, data: Dict, prefix: str = "news") -> str:
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
    
    def calculate_buzz_score(self, articles: List[Dict]) -> float:
        """
        記事のバズスコアを計算
        
        Args:
            articles: 記事データのリスト
            
        Returns:
            バズスコア（0-1の範囲）
        """
        if not articles:
            return 0.0
        
        # 記事数による基本スコア
        article_score = min(len(articles) / 100, 1.0)  # 100記事で最大値
        
        # 時間的分散（最近の記事が多いほど高スコア）
        recent_articles = 0
        for article in articles:
            published = article.get('publishedAt', '')
            if published:
                pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                days_ago = (datetime.now(pub_date.tzinfo) - pub_date).days
                if days_ago <= 7:
                    recent_articles += 1
        
        recency_score = recent_articles / len(articles) if articles else 0
        
        # センチメント（ポジティブなほど高スコア）
        sentiment = self.analyze_sentiment(articles)
        sentiment_score = (sentiment['polarity'] + 1) / 2  # -1~1 を 0~1 に正規化
        
        # 総合スコア（重み付け平均）
        buzz_score = (
            article_score * 0.4 +
            recency_score * 0.4 +
            sentiment_score * 0.2
        )
        
        return round(buzz_score, 3)


def main():
    """メイン実行関数（テスト用）"""
    logger.info("=== News Collector Test ===")
    
    # コレクター初期化
    collector = NewsCollector()
    
    # テスト用キーワード
    industry_keywords = ["cosmetics", "beauty", "skincare"]
    product_keywords = ["vitamin C", "retinol", "hyaluronic acid", "niacinamide"]
    
    # ニュース収集
    logger.info("\nCollecting industry news...")
    results = collector.collect_industry_news(
        industry_keywords=industry_keywords,
        product_keywords=product_keywords,
        days_back=7
    )
    
    # 結果表示
    logger.info("\n=== Collection Results ===")
    logger.info(f"Total articles: {results['total_articles']}")
    logger.info(f"Sentiment: {results['sentiment']['sentiment_label']} "
               f"(polarity: {results['sentiment']['polarity']:.3f})")
    
    if results['trends']['keywords']:
        logger.info("\nTop Keywords:")
        for keyword, count in sorted(
            results['trends']['keywords'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]:
            logger.info(f"  - {keyword}: {count} articles")
    
    if results['articles']:
        # バズスコア計算
        buzz_score = collector.calculate_buzz_score(results['articles'])
        logger.info(f"\nBuzz Score: {buzz_score:.3f}")
        
        logger.info("\nTop Articles:")
        for article in results['trends']['top_articles'][:3]:
            logger.info(f"  - {article['title']}")
            logger.info(f"    Source: {article['source']}")
    
    logger.info("\n✅ News collection test completed!")
    
    return results


if __name__ == "__main__":
    # テスト実行
    main()