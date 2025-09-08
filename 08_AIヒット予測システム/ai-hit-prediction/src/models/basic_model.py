"""
基本的なヒット予測モデル
ランダムフォレストを使用した二値分類モデル
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import joblib
import os
import logging
from typing import Optional, Tuple, Dict
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HitPredictionModel:
    """ヒット商品を予測するランダムフォレストモデル"""
    
    def __init__(self, model_dir: str = "data/models"):
        """
        初期化
        
        Args:
            model_dir: モデル保存先ディレクトリ
        """
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1  # 全CPUコアを使用
        )
        self.is_trained = False
        self.model_dir = model_dir
        self.feature_names = None
        self.model_metrics = {}
        self._ensure_model_dir()
        
    def _ensure_model_dir(self):
        """モデルディレクトリが存在することを確認"""
        os.makedirs(self.model_dir, exist_ok=True)
        logger.info(f"Model directory ensured: {self.model_dir}")
    
    def prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        特徴量を準備（Phase 1では仮のデータを生成）
        
        Args:
            data: 入力データ
            
        Returns:
            特徴量データフレーム
        """
        # Phase 1: 仮の特徴量を生成
        # Phase 2以降で実際のAPI取得データに置き換え
        n_samples = len(data)
        
        features = pd.DataFrame({
            # 科学的トレンド関連
            'scientific_trend_score': np.random.uniform(0, 1, n_samples),
            'paper_citation_count': np.random.randint(0, 100, n_samples),
            'recent_paper_ratio': np.random.uniform(0, 1, n_samples),
            
            # ソーシャルメディア関連
            'social_mentions': np.random.randint(0, 1000, n_samples),
            'influencer_count': np.random.randint(0, 50, n_samples),
            'engagement_rate': np.random.uniform(0, 0.1, n_samples),
            
            # 市場関連
            'price_range': np.random.choice([1, 2, 3, 4, 5], n_samples),  # 1:低価格〜5:高価格
            'competitor_count': np.random.randint(1, 20, n_samples),
            'market_saturation': np.random.uniform(0, 1, n_samples),
            
            # 製品特性
            'ingredient_novelty': np.random.uniform(0, 1, n_samples),
            'brand_strength': np.random.uniform(0, 1, n_samples),
            'seasonality_factor': np.random.uniform(0, 1, n_samples)
        })
        
        self.feature_names = features.columns.tolist()
        logger.info(f"Prepared {len(features.columns)} features for {n_samples} samples")
        
        return features
    
    def train(self, X: pd.DataFrame, y: np.ndarray, 
              test_size: float = 0.2, 
              validate: bool = True) -> Dict:
        """
        モデルを学習
        
        Args:
            X: 特徴量データ
            y: ターゲットラベル（0: 非ヒット, 1: ヒット）
            test_size: テストデータの割合
            validate: 交差検証を実行するか
            
        Returns:
            学習結果のメトリクス
        """
        logger.info("Starting model training...")
        
        # データ分割
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        # モデル学習
        self.model.fit(X_train, y_train)
        self.is_trained = True
        
        # 予測
        y_train_pred = self.model.predict(X_train)
        y_test_pred = self.model.predict(X_test)
        y_test_proba = self.model.predict_proba(X_test)[:, 1]
        
        # メトリクス計算
        self.model_metrics = {
            'train': {
                'accuracy': accuracy_score(y_train, y_train_pred),
                'precision': precision_score(y_train, y_train_pred),
                'recall': recall_score(y_train, y_train_pred),
                'f1': f1_score(y_train, y_train_pred)
            },
            'test': {
                'accuracy': accuracy_score(y_test, y_test_pred),
                'precision': precision_score(y_test, y_test_pred),
                'recall': recall_score(y_test, y_test_pred),
                'f1': f1_score(y_test, y_test_pred),
                'auc': roc_auc_score(y_test, y_test_proba)
            }
        }
        
        # 交差検証
        if validate:
            cv_scores = cross_val_score(self.model, X, y, cv=5, scoring='f1')
            self.model_metrics['cv_f1_mean'] = cv_scores.mean()
            self.model_metrics['cv_f1_std'] = cv_scores.std()
        
        # 結果表示
        self._print_metrics()
        
        # 特徴量重要度
        self._analyze_feature_importance()
        
        return self.model_metrics
    
    def _print_metrics(self):
        """学習結果のメトリクスを表示"""
        logger.info("\n=== Model Performance ===")
        logger.info("Training Set:")
        for metric, value in self.model_metrics['train'].items():
            logger.info(f"  {metric.capitalize()}: {value:.3f}")
        
        logger.info("\nTest Set:")
        for metric, value in self.model_metrics['test'].items():
            logger.info(f"  {metric.capitalize()}: {value:.3f}")
        
        if 'cv_f1_mean' in self.model_metrics:
            logger.info(f"\nCross-validation F1: {self.model_metrics['cv_f1_mean']:.3f} "
                       f"(+/- {self.model_metrics['cv_f1_std']:.3f})")
    
    def _analyze_feature_importance(self):
        """特徴量の重要度を分析"""
        if self.feature_names:
            importance = pd.DataFrame({
                'feature': self.feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            logger.info("\n=== Top 5 Important Features ===")
            for _, row in importance.head(5).iterrows():
                logger.info(f"  {row['feature']}: {row['importance']:.3f}")
            
            self.model_metrics['feature_importance'] = importance.to_dict('records')
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        予測を実行（確率）
        
        Args:
            X: 特徴量データ
            
        Returns:
            ヒット確率の配列
        """
        if not self.is_trained:
            raise Exception("Model not trained yet. Please train the model first.")
        
        probabilities = self.model.predict_proba(X)[:, 1]
        return probabilities
    
    def predict_with_confidence(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        予測結果と信頼度を返す
        
        Args:
            X: 特徴量データ
            
        Returns:
            予測結果と信頼度を含むデータフレーム
        """
        if not self.is_trained:
            raise Exception("Model not trained yet")
        
        # 各決定木の予測を取得
        predictions = np.array([tree.predict_proba(X)[:, 1] 
                               for tree in self.model.estimators_])
        
        # 平均と標準偏差を計算
        mean_prob = predictions.mean(axis=0)
        std_prob = predictions.std(axis=0)
        
        results = pd.DataFrame({
            'hit_probability': mean_prob,
            'confidence': 1 - std_prob,  # 標準偏差が低いほど信頼度が高い
            'prediction': (mean_prob >= 0.5).astype(int),
            'risk_level': pd.cut(mean_prob, 
                                bins=[0, 0.3, 0.5, 0.7, 1.0],
                                labels=['High Risk', 'Medium Risk', 'Medium Potential', 'High Potential'])
        })
        
        return results
    
    def save_model(self, filename: Optional[str] = None) -> str:
        """
        モデルを保存
        
        Args:
            filename: 保存ファイル名（指定しない場合は自動生成）
            
        Returns:
            保存したファイルパス
        """
        if not self.is_trained:
            raise Exception("Model not trained yet")
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"model_{timestamp}.pkl"
        
        filepath = os.path.join(self.model_dir, filename)
        
        # モデルとメタデータを保存
        model_data = {
            'model': self.model,
            'feature_names': self.feature_names,
            'metrics': self.model_metrics,
            'version': '1.0',
            'trained_at': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        logger.info(f"Model saved to: {filepath}")
        
        return filepath
    
    def load_model(self, filepath: str):
        """
        モデルを読み込み
        
        Args:
            filepath: 読み込むモデルファイルのパス
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.feature_names = model_data.get('feature_names')
        self.model_metrics = model_data.get('metrics', {})
        self.is_trained = True
        
        logger.info(f"Model loaded from: {filepath}")
        logger.info(f"Model trained at: {model_data.get('trained_at', 'Unknown')}")


def generate_dummy_data(n_samples: int = 1000) -> Tuple[pd.DataFrame, np.ndarray]:
    """
    テスト用のダミーデータを生成
    
    Args:
        n_samples: サンプル数
        
    Returns:
        データフレームとラベルのタプル
    """
    # 商品IDを生成
    data = pd.DataFrame({
        'product_id': [f'PROD_{i:04d}' for i in range(n_samples)],
        'product_name': [f'Product {i}' for i in range(n_samples)]
    })
    
    # ラベルを生成（30%がヒット）
    y = np.random.choice([0, 1], size=n_samples, p=[0.7, 0.3])
    
    return data, y


def main():
    """メイン実行関数（テスト用）"""
    logger.info("=== Hit Prediction Model Test ===")
    
    # ダミーデータ生成
    logger.info("\nGenerating dummy data...")
    data, labels = generate_dummy_data(n_samples=500)
    logger.info(f"Generated {len(data)} samples")
    logger.info(f"Hit ratio: {labels.mean():.1%}")
    
    # モデル初期化
    model = HitPredictionModel()
    
    # 特徴量準備
    logger.info("\nPreparing features...")
    X = model.prepare_features(data)
    
    # モデル学習
    logger.info("\nTraining model...")
    metrics = model.train(X, labels)
    
    # 新商品の予測テスト
    logger.info("\n=== Testing Prediction for New Products ===")
    new_products = pd.DataFrame({
        'product_id': ['NEW_001', 'NEW_002', 'NEW_003'],
        'product_name': ['Super Serum', 'Magic Cream', 'Wonder Toner']
    })
    
    X_new = model.prepare_features(new_products)
    predictions = model.predict_with_confidence(X_new)
    
    # 結果表示
    for i, row in predictions.iterrows():
        logger.info(f"\n{new_products.iloc[i]['product_name']}:")
        logger.info(f"  Hit Probability: {row['hit_probability']:.1%}")
        logger.info(f"  Confidence: {row['confidence']:.1%}")
        logger.info(f"  Risk Level: {row['risk_level']}")
    
    # モデル保存
    logger.info("\nSaving model...")
    model_path = model.save_model("basic_model_v1.pkl")
    
    # モデル読み込みテスト
    logger.info("\nTesting model loading...")
    new_model = HitPredictionModel()
    new_model.load_model(model_path)
    
    # 読み込んだモデルで予測
    reload_predictions = new_model.predict(X_new)
    logger.info(f"Predictions after reload: {reload_predictions}")
    
    logger.info("\n✅ Model test completed successfully!")
    
    return model


if __name__ == "__main__":
    # テスト実行
    model = main()