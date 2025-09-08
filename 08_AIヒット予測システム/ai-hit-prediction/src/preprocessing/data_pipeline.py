"""
データパイプライン
複数のデータソースを統合し、モデル用の特徴量を生成
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
from pathlib import Path
import glob

# プロジェクトルートをパスに追加
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.data_collection.academic_collector import AcademicPaperCollector
from src.data_collection.news_collector import NewsCollector

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataPipeline:
    """データ収集から特徴量生成までの統合パイプライン"""
    
    def __init__(self, 
                 raw_data_path: str = "data/raw",
                 processed_data_path: str = "data/processed"):
        """
        初期化
        
        Args:
            raw_data_path: 生データの保存先
            processed_data_path: 処理済みデータの保存先
        """
        self.raw_data_path = raw_data_path
        self.processed_data_path = processed_data_path
        self._ensure_directories()
        
        # データコレクター初期化
        self.academic_collector = AcademicPaperCollector(data_dir=raw_data_path)
        self.news_collector = NewsCollector(data_dir=raw_data_path)
        
        # キャッシュ
        self._data_cache = {}
        
    def _ensure_directories(self):
        """必要なディレクトリを作成"""
        os.makedirs(self.raw_data_path, exist_ok=True)
        os.makedirs(self.processed_data_path, exist_ok=True)
        logger.info(f"Directories ensured: {self.raw_data_path}, {self.processed_data_path}")
    
    def collect_all_data(self, 
                        keywords: List[str],
                        days_back: int = 30) -> Dict[str, Any]:
        """
        すべてのデータソースから情報を収集
        
        Args:
            keywords: 検索キーワードのリスト
            days_back: 何日前までのデータを取得するか
            
        Returns:
            収集したデータの辞書
        """
        logger.info("Starting comprehensive data collection...")
        
        collected_data = {
            'timestamp': datetime.now().isoformat(),
            'keywords': keywords,
            'academic': {},
            'news': {},
            'social': {}  # Phase 3で実装
        }
        
        # 1. 学術データ収集
        logger.info("Collecting academic papers...")
        try:
            academic_results = self.academic_collector.collect_papers_for_keywords(
                keywords=keywords,
                papers_per_keyword=10
            )
            collected_data['academic'] = academic_results
            logger.info(f"Collected academic data for {len(academic_results)} keywords")
        except Exception as e:
            logger.error(f"Failed to collect academic data: {e}")
            collected_data['academic'] = {}
        
        # 2. ニュースデータ収集
        logger.info("Collecting news articles...")
        try:
            news_results = self.news_collector.search_news(
                keywords=keywords,
                days_back=days_back
            )
            collected_data['news'] = news_results
            logger.info(f"Collected {news_results.get('totalResults', 0)} news articles")
        except Exception as e:
            logger.error(f"Failed to collect news data: {e}")
            collected_data['news'] = {}
        
        # 3. データ保存
        self._save_collected_data(collected_data)
        
        return collected_data
    
    def _save_collected_data(self, data: Dict[str, Any]) -> str:
        """収集したデータを保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.raw_data_path, f"collected_data_{timestamp}.json")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Collected data saved to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save collected data: {e}")
            return ""
    
    def load_latest_data(self, data_type: str = "all") -> Optional[Dict]:
        """
        最新の収集データを読み込み
        
        Args:
            data_type: "all", "academic", "news", "papers" のいずれか
            
        Returns:
            データの辞書、見つからない場合はNone
        """
        pattern_map = {
            "all": "collected_data_*.json",
            "academic": "cosmetics_papers_*.json",
            "papers": "papers_*.json",
            "news": "industry_news_*.json"
        }
        
        pattern = pattern_map.get(data_type, "collected_data_*.json")
        files = glob.glob(os.path.join(self.raw_data_path, pattern))
        
        if not files:
            logger.warning(f"No data files found for type: {data_type}")
            return None
        
        # 最新のファイルを選択
        latest_file = max(files, key=os.path.getctime)
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.info(f"Loaded data from: {latest_file}")
            return data
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
            return None
    
    def extract_features(self, product_info: Dict[str, Any]) -> pd.DataFrame:
        """
        製品情報から特徴量を抽出
        
        Args:
            product_info: 製品情報の辞書
            
        Returns:
            特徴量のDataFrame
        """
        features = {}
        
        # 製品基本情報
        product_name = product_info.get('name', '')
        keywords = product_info.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [keywords]
        
        # 最新データを読み込み
        collected_data = self.load_latest_data("all")
        
        if collected_data:
            # 学術トレンド特徴量
            academic_features = self._extract_academic_features(
                collected_data.get('academic', {}), 
                keywords
            )
            features.update(academic_features)
            
            # ニューストレンド特徴量
            news_features = self._extract_news_features(
                collected_data.get('news', {}), 
                keywords
            )
            features.update(news_features)
        else:
            # デフォルト値を設定
            features = self._get_default_features()
        
        # 製品固有の特徴量を追加
        features.update(self._extract_product_features(product_info))
        
        # DataFrameに変換
        df = pd.DataFrame([features])
        
        return df
    
    def _extract_academic_features(self, 
                                  academic_data: Dict, 
                                  keywords: List[str]) -> Dict[str, float]:
        """学術データから特徴量を抽出"""
        features = {
            'academic_paper_count': 0,
            'academic_avg_citations': 0.0,
            'academic_recent_ratio': 0.0,
            'academic_trend_score': 0.0
        }
        
        if not academic_data or not keywords:
            return features
        
        all_papers = []
        for keyword in keywords:
            papers = academic_data.get(keyword, [])
            all_papers.extend(papers)
        
        if all_papers:
            # 論文数
            features['academic_paper_count'] = len(all_papers)
            
            # 平均引用数
            citations = [p.get('citationCount', 0) or 0 for p in all_papers]
            features['academic_avg_citations'] = np.mean(citations) if citations else 0
            
            # 最近の論文の割合（2020年以降）
            recent = sum(1 for p in all_papers if p.get('year', 0) and p['year'] >= 2020)
            features['academic_recent_ratio'] = recent / len(all_papers) if all_papers else 0
            
            # トレンドスコア（論文数と引用数の組み合わせ）
            features['academic_trend_score'] = min(
                (features['academic_paper_count'] / 100) * 0.5 +
                (features['academic_avg_citations'] / 50) * 0.5,
                1.0
            )
        
        return features
    
    def _extract_news_features(self, 
                              news_data: Dict, 
                              keywords: List[str]) -> Dict[str, float]:
        """ニュースデータから特徴量を抽出"""
        features = {
            'news_article_count': 0,
            'news_buzz_score': 0.0,
            'news_sentiment_score': 0.0,
            'news_recency_score': 0.0
        }
        
        if not news_data:
            return features
        
        articles = news_data.get('articles', [])
        
        if articles:
            # 記事数
            features['news_article_count'] = len(articles)
            
            # バズスコア（記事数ベース）
            features['news_buzz_score'] = min(len(articles) / 50, 1.0)
            
            # 最近の記事の割合
            recent_articles = 0
            for article in articles:
                published = article.get('publishedAt', '')
                if published:
                    try:
                        pub_date = datetime.fromisoformat(published.replace('Z', '+00:00'))
                        days_ago = (datetime.now(pub_date.tzinfo) - pub_date).days
                        if days_ago <= 7:
                            recent_articles += 1
                    except:
                        pass
            
            features['news_recency_score'] = recent_articles / len(articles) if articles else 0
            
            # センチメントスコア（簡易版）
            # Phase 2では中立的な値を設定
            features['news_sentiment_score'] = 0.5
        
        return features
    
    def _extract_product_features(self, product_info: Dict) -> Dict[str, float]:
        """製品情報から特徴量を抽出"""
        features = {}
        
        # 価格帯（1-5の範囲）
        price = product_info.get('price', 5000)
        if price < 2000:
            features['price_range'] = 1
        elif price < 5000:
            features['price_range'] = 2
        elif price < 10000:
            features['price_range'] = 3
        elif price < 20000:
            features['price_range'] = 4
        else:
            features['price_range'] = 5
        
        # ブランド力（仮の値）
        features['brand_strength'] = product_info.get('brand_strength', 0.5)
        
        # 成分の新規性（仮の値）
        features['ingredient_novelty'] = product_info.get('ingredient_novelty', 0.5)
        
        # 競合数（仮の値）
        features['competitor_count'] = product_info.get('competitor_count', 10)
        
        # 市場飽和度（仮の値）
        features['market_saturation'] = product_info.get('market_saturation', 0.5)
        
        # 季節性要因（仮の値）
        features['seasonality_factor'] = product_info.get('seasonality_factor', 0.5)
        
        return features
    
    def _get_default_features(self) -> Dict[str, float]:
        """デフォルトの特徴量値を返す"""
        return {
            # 学術関連
            'academic_paper_count': 0,
            'academic_avg_citations': 0.0,
            'academic_recent_ratio': 0.0,
            'academic_trend_score': 0.0,
            
            # ニュース関連
            'news_article_count': 0,
            'news_buzz_score': 0.0,
            'news_sentiment_score': 0.5,
            'news_recency_score': 0.0,
            
            # 製品関連
            'price_range': 3,
            'brand_strength': 0.5,
            'ingredient_novelty': 0.5,
            'competitor_count': 10,
            'market_saturation': 0.5,
            'seasonality_factor': 0.5
        }
    
    def prepare_training_data(self, 
                             products: List[Dict],
                             labels: Optional[List[int]] = None) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        複数の製品情報から学習用データを準備
        
        Args:
            products: 製品情報のリスト
            labels: ラベル（ヒット=1, 非ヒット=0）のリスト
            
        Returns:
            特徴量DataFrameとラベル配列のタプル
        """
        all_features = []
        
        for product in products:
            features = self.extract_features(product)
            all_features.append(features)
        
        # 特徴量を結合
        X = pd.concat(all_features, ignore_index=True)
        
        # ラベルが提供されていない場合は仮のラベルを生成
        if labels is None:
            # 仮のラベル生成（30%がヒット）
            y = np.random.choice([0, 1], size=len(products), p=[0.7, 0.3])
        else:
            y = np.array(labels)
        
        logger.info(f"Prepared training data: {X.shape[0]} samples, {X.shape[1]} features")
        
        return X, y
    
    def save_processed_data(self, 
                           features: pd.DataFrame,
                           labels: Optional[np.ndarray] = None,
                           prefix: str = "processed") -> str:
        """
        処理済みデータを保存
        
        Args:
            features: 特徴量DataFrame
            labels: ラベル配列（オプション）
            prefix: ファイル名のプレフィックス
            
        Returns:
            保存したファイルパス
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 特徴量を保存
        features_file = os.path.join(
            self.processed_data_path, 
            f"{prefix}_features_{timestamp}.csv"
        )
        features.to_csv(features_file, index=False)
        logger.info(f"Features saved to: {features_file}")
        
        # ラベルがある場合は保存
        if labels is not None:
            labels_file = os.path.join(
                self.processed_data_path,
                f"{prefix}_labels_{timestamp}.npy"
            )
            np.save(labels_file, labels)
            logger.info(f"Labels saved to: {labels_file}")
        
        return features_file


def main():
    """メイン実行関数（テスト用）"""
    logger.info("=== Data Pipeline Test ===")
    
    # パイプライン初期化
    pipeline = DataPipeline()
    
    # テスト用キーワード
    keywords = ["vitamin C", "retinol", "hyaluronic acid"]
    
    # データ収集
    logger.info("\n1. Collecting data from all sources...")
    collected_data = pipeline.collect_all_data(keywords, days_back=7)
    
    # サンプル製品情報
    test_products = [
        {
            'name': 'Premium Vitamin C Serum',
            'keywords': ['vitamin C', 'brightening'],
            'price': 8000,
            'brand_strength': 0.8
        },
        {
            'name': 'Retinol Night Cream',
            'keywords': ['retinol', 'anti-aging'],
            'price': 12000,
            'ingredient_novelty': 0.7
        },
        {
            'name': 'Hydrating HA Toner',
            'keywords': ['hyaluronic acid', 'hydration'],
            'price': 3000,
            'competitor_count': 15
        }
    ]
    
    # 特徴量抽出
    logger.info("\n2. Extracting features for test products...")
    for product in test_products:
        logger.info(f"\nProduct: {product['name']}")
        features = pipeline.extract_features(product)
        logger.info(f"Features shape: {features.shape}")
        logger.info(f"Feature columns: {features.columns.tolist()}")
        
        # 主要な特徴量を表示
        for col in ['academic_trend_score', 'news_buzz_score', 'price_range']:
            if col in features.columns:
                logger.info(f"  {col}: {features[col].iloc[0]:.3f}")
    
    # 学習用データ準備
    logger.info("\n3. Preparing training data...")
    X, y = pipeline.prepare_training_data(test_products)
    logger.info(f"Training data shape: X={X.shape}, y={y.shape}")
    logger.info(f"Hit ratio in labels: {y.mean():.1%}")
    
    # データ保存
    logger.info("\n4. Saving processed data...")
    saved_file = pipeline.save_processed_data(X, y, prefix="test")
    
    logger.info("\n✅ Data pipeline test completed!")
    
    return pipeline, X, y


if __name__ == "__main__":
    # テスト実行
    main()