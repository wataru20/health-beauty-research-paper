"""
特徴量エンジニアリング
データから高度な特徴量を生成
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
from sklearn.preprocessing import StandardScaler, LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    """特徴量エンジニアリングクラス"""
    
    def __init__(self):
        """初期化"""
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.feature_importance = {}
        
    def create_advanced_features(self, base_features: pd.DataFrame) -> pd.DataFrame:
        """
        基本特徴量から高度な特徴量を生成
        
        Args:
            base_features: 基本特徴量のDataFrame
            
        Returns:
            拡張された特徴量のDataFrame
        """
        features = base_features.copy()
        
        # 1. 交互作用特徴量
        features = self._create_interaction_features(features)
        
        # 2. 比率特徴量
        features = self._create_ratio_features(features)
        
        # 3. 集約特徴量
        features = self._create_aggregate_features(features)
        
        # 4. トレンド強度特徴量
        features = self._create_trend_features(features)
        
        # 5. リスクスコア
        features = self._create_risk_scores(features)
        
        logger.info(f"Created {features.shape[1]} features (original: {base_features.shape[1]})")
        
        return features
    
    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """交互作用特徴量を生成"""
        # 学術トレンド × ニューストレンド
        if 'academic_trend_score' in df.columns and 'news_buzz_score' in df.columns:
            df['trend_synergy'] = df['academic_trend_score'] * df['news_buzz_score']
        
        # 価格 × ブランド力
        if 'price_range' in df.columns and 'brand_strength' in df.columns:
            df['premium_positioning'] = df['price_range'] * df['brand_strength']
        
        # 新規性 × 市場飽和度
        if 'ingredient_novelty' in df.columns and 'market_saturation' in df.columns:
            df['innovation_opportunity'] = df['ingredient_novelty'] * (1 - df['market_saturation'])
        
        return df
    
    def _create_ratio_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """比率特徴量を生成"""
        # 引用数対論文数比
        if 'academic_avg_citations' in df.columns and 'academic_paper_count' in df.columns:
            df['citation_efficiency'] = df.apply(
                lambda x: x['academic_avg_citations'] / max(x['academic_paper_count'], 1),
                axis=1
            )
        
        # ニュース新鮮度比
        if 'news_recency_score' in df.columns and 'news_article_count' in df.columns:
            df['news_freshness_ratio'] = df.apply(
                lambda x: x['news_recency_score'] * min(x['news_article_count'] / 10, 1),
                axis=1
            )
        
        # 競合対比スコア
        if 'competitor_count' in df.columns:
            df['competitive_advantage'] = df.apply(
                lambda x: 1 / (1 + x['competitor_count']),
                axis=1
            )
        
        return df
    
    def _create_aggregate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """集約特徴量を生成"""
        # 総合学術スコア
        academic_cols = [col for col in df.columns if col.startswith('academic_')]
        if academic_cols:
            df['academic_overall_score'] = df[academic_cols].mean(axis=1)
        
        # 総合メディアスコア
        news_cols = [col for col in df.columns if col.startswith('news_')]
        if news_cols:
            df['media_overall_score'] = df[news_cols].mean(axis=1)
        
        # 市場ポテンシャルスコア
        market_features = ['brand_strength', 'ingredient_novelty', 'competitive_advantage']
        available_features = [f for f in market_features if f in df.columns]
        if available_features:
            df['market_potential_score'] = df[available_features].mean(axis=1)
        
        return df
    
    def _create_trend_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """トレンド強度特徴量を生成"""
        # トレンドモメンタム（学術×ニュース×最新度）
        if all(col in df.columns for col in ['academic_trend_score', 'news_buzz_score', 'academic_recent_ratio']):
            df['trend_momentum'] = (
                df['academic_trend_score'] * 0.3 +
                df['news_buzz_score'] * 0.3 +
                df['academic_recent_ratio'] * 0.4
            )
        
        # イノベーション指数
        if all(col in df.columns for col in ['ingredient_novelty', 'academic_recent_ratio']):
            df['innovation_index'] = (
                df['ingredient_novelty'] * df['academic_recent_ratio']
            )
        
        # バイラルポテンシャル
        if 'news_buzz_score' in df.columns and 'news_sentiment_score' in df.columns:
            df['viral_potential'] = df['news_buzz_score'] * df['news_sentiment_score']
        
        return df
    
    def _create_risk_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """リスクスコアを計算"""
        # 市場リスク
        risk_factors = []
        
        if 'market_saturation' in df.columns:
            risk_factors.append(df['market_saturation'])
        
        if 'competitor_count' in df.columns:
            risk_factors.append(df['competitor_count'] / df['competitor_count'].max())
        
        if 'price_range' in df.columns:
            # 価格が極端（低すぎor高すぎ）な場合のリスク
            price_risk = df['price_range'].apply(
                lambda x: abs(x - 3) / 2  # 中価格帯（3）からの距離
            )
            risk_factors.append(price_risk)
        
        if risk_factors:
            df['market_risk_score'] = pd.concat(risk_factors, axis=1).mean(axis=1)
        
        # トレンドリスク（トレンドが弱い場合のリスク）
        trend_features = ['academic_trend_score', 'news_buzz_score']
        available_trend = [f for f in trend_features if f in df.columns]
        if available_trend:
            df['trend_risk_score'] = 1 - df[available_trend].mean(axis=1)
        
        # 総合リスクスコア
        risk_cols = [col for col in df.columns if col.endswith('_risk_score')]
        if risk_cols:
            df['overall_risk_score'] = df[risk_cols].mean(axis=1)
        
        return df
    
    def normalize_features(self, 
                          features: pd.DataFrame,
                          exclude_cols: Optional[List[str]] = None) -> pd.DataFrame:
        """
        特徴量を正規化
        
        Args:
            features: 特徴量DataFrame
            exclude_cols: 正規化から除外するカラム
            
        Returns:
            正規化された特徴量DataFrame
        """
        if exclude_cols is None:
            exclude_cols = []
        
        # 数値カラムのみ選択
        numeric_cols = features.select_dtypes(include=[np.number]).columns.tolist()
        cols_to_normalize = [col for col in numeric_cols if col not in exclude_cols]
        
        if cols_to_normalize:
            features[cols_to_normalize] = self.scaler.fit_transform(features[cols_to_normalize])
            logger.info(f"Normalized {len(cols_to_normalize)} features")
        
        return features
    
    def select_top_features(self, 
                          features: pd.DataFrame,
                          importance_scores: Optional[Dict[str, float]] = None,
                          top_n: int = 20) -> pd.DataFrame:
        """
        重要度の高い特徴量を選択
        
        Args:
            features: 特徴量DataFrame
            importance_scores: 特徴量の重要度スコア
            top_n: 選択する特徴量数
            
        Returns:
            選択された特徴量のDataFrame
        """
        if importance_scores is None:
            # デフォルトの重要度（分散ベース）
            importance_scores = {}
            for col in features.select_dtypes(include=[np.number]).columns:
                importance_scores[col] = features[col].var()
        
        # 重要度でソート
        sorted_features = sorted(importance_scores.items(), key=lambda x: x[1], reverse=True)
        top_features = [f[0] for f in sorted_features[:top_n]]
        
        # 存在するカラムのみ選択
        selected_cols = [col for col in top_features if col in features.columns]
        
        logger.info(f"Selected top {len(selected_cols)} features")
        
        return features[selected_cols]
    
    def create_categorical_features(self, 
                                   features: pd.DataFrame,
                                   numerical_cols: List[str]) -> pd.DataFrame:
        """
        数値特徴量をカテゴリカル特徴量に変換
        
        Args:
            features: 特徴量DataFrame
            numerical_cols: 変換対象のカラム
            
        Returns:
            カテゴリカル特徴量を追加したDataFrame
        """
        for col in numerical_cols:
            if col in features.columns:
                # 四分位数でカテゴリ分け
                features[f'{col}_category'] = pd.qcut(
                    features[col], 
                    q=4, 
                    labels=['low', 'medium_low', 'medium_high', 'high'],
                    duplicates='drop'
                )
        
        return features
    
    def get_feature_summary(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        特徴量のサマリー統計を取得
        
        Args:
            features: 特徴量DataFrame
            
        Returns:
            サマリー統計のDataFrame
        """
        summary = features.describe().T
        summary['missing'] = features.isnull().sum()
        summary['unique'] = features.nunique()
        summary['dtype'] = features.dtypes
        
        return summary


def create_model_ready_features(raw_features: pd.DataFrame,
                               target: Optional[pd.Series] = None) -> pd.DataFrame:
    """
    モデル投入可能な特徴量セットを作成
    
    Args:
        raw_features: 生の特徴量DataFrame
        target: ターゲット変数（オプション）
        
    Returns:
        モデル用の特徴量DataFrame
    """
    engineer = FeatureEngineer()
    
    # 1. 高度な特徴量を生成
    enhanced_features = engineer.create_advanced_features(raw_features)
    
    # 2. 欠損値処理
    enhanced_features = enhanced_features.fillna(0)
    
    # 3. 正規化（カテゴリカル以外）
    categorical_cols = enhanced_features.select_dtypes(include=['object', 'category']).columns.tolist()
    enhanced_features = engineer.normalize_features(enhanced_features, exclude_cols=categorical_cols)
    
    # 4. 特徴量選択（targetがある場合は相関ベース）
    if target is not None:
        # 相関係数を計算
        correlations = {}
        for col in enhanced_features.select_dtypes(include=[np.number]).columns:
            if col in enhanced_features.columns:
                correlations[col] = abs(enhanced_features[col].corr(target))
        
        enhanced_features = engineer.select_top_features(
            enhanced_features, 
            importance_scores=correlations
        )
    
    logger.info(f"Final feature shape: {enhanced_features.shape}")
    
    return enhanced_features


def main():
    """メイン実行関数（テスト用）"""
    logger.info("=== Feature Engineering Test ===")
    
    # サンプルデータ生成
    sample_data = pd.DataFrame({
        'academic_trend_score': np.random.uniform(0, 1, 100),
        'academic_paper_count': np.random.randint(0, 50, 100),
        'academic_avg_citations': np.random.uniform(0, 100, 100),
        'academic_recent_ratio': np.random.uniform(0, 1, 100),
        'news_buzz_score': np.random.uniform(0, 1, 100),
        'news_article_count': np.random.randint(0, 100, 100),
        'news_sentiment_score': np.random.uniform(0, 1, 100),
        'news_recency_score': np.random.uniform(0, 1, 100),
        'price_range': np.random.randint(1, 6, 100),
        'brand_strength': np.random.uniform(0, 1, 100),
        'ingredient_novelty': np.random.uniform(0, 1, 100),
        'competitor_count': np.random.randint(1, 30, 100),
        'market_saturation': np.random.uniform(0, 1, 100),
        'seasonality_factor': np.random.uniform(0, 1, 100)
    })
    
    logger.info(f"Original features: {sample_data.shape}")
    
    # 特徴量エンジニアリング
    engineer = FeatureEngineer()
    
    # 1. 高度な特徴量生成
    enhanced_features = engineer.create_advanced_features(sample_data)
    logger.info(f"\nAfter feature engineering: {enhanced_features.shape}")
    
    # 新しく作成された特徴量を表示
    new_features = [col for col in enhanced_features.columns if col not in sample_data.columns]
    logger.info(f"\nNew features created ({len(new_features)}):")
    for feature in new_features:
        logger.info(f"  - {feature}")
    
    # 2. 特徴量サマリー
    summary = engineer.get_feature_summary(enhanced_features)
    logger.info(f"\nFeature summary (top 5):")
    logger.info(summary.head())
    
    # 3. モデル用特徴量作成
    target = pd.Series(np.random.choice([0, 1], 100))
    model_features = create_model_ready_features(sample_data, target)
    logger.info(f"\nModel-ready features: {model_features.shape}")
    
    logger.info("\n✅ Feature engineering test completed!")
    
    return enhanced_features


if __name__ == "__main__":
    # テスト実行
    main()