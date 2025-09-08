#!/usr/bin/env python
"""
拡張版モデルトレーニングスクリプト
Phase 2の新機能を活用した高度なモデル学習
"""

import sys
import os
import pandas as pd
import numpy as np
import logging
from datetime import datetime
import json
import joblib
from typing import Dict, Tuple, Optional

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.basic_model import HitPredictionModel
from src.preprocessing.data_pipeline import DataPipeline
from src.preprocessing.feature_engineering import FeatureEngineer, create_model_ready_features
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import classification_report, confusion_matrix
import warnings
warnings.filterwarnings('ignore')

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedModelTrainer:
    """拡張版モデルトレーナー"""
    
    def __init__(self, model_dir: str = "data/models"):
        """
        初期化
        
        Args:
            model_dir: モデル保存先ディレクトリ
        """
        self.model_dir = model_dir
        self.pipeline = DataPipeline()
        self.feature_engineer = FeatureEngineer()
        self.model = None
        self.best_params = None
        self.training_history = []
        
    def prepare_data(self, 
                    products_file: Optional[str] = None,
                    use_real_data: bool = False) -> Tuple[pd.DataFrame, np.ndarray]:
        """
        学習データを準備
        
        Args:
            products_file: 製品情報ファイルパス
            use_real_data: 実データを使用するか（APIから取得）
            
        Returns:
            特徴量とラベルのタプル
        """
        logger.info("Preparing training data...")
        
        if products_file and os.path.exists(products_file):
            # ファイルから製品データを読み込み
            products = pd.read_csv(products_file)
            logger.info(f"Loaded {len(products)} products from file")
        else:
            # サンプルデータを生成
            products = self._generate_sample_products(100)
            logger.info(f"Generated {len(products)} sample products")
        
        # データ収集（実データを使用する場合）
        if use_real_data:
            logger.info("Collecting real data from APIs...")
            keywords = self._extract_keywords(products)
            self.pipeline.collect_all_data(keywords[:10], days_back=30)
        
        # 特徴量抽出
        all_features = []
        for _, product in products.iterrows():
            product_dict = product.to_dict()
            features = self.pipeline.extract_features(product_dict)
            all_features.append(features)
        
        # 特徴量を結合
        X = pd.concat(all_features, ignore_index=True)
        
        # 高度な特徴量エンジニアリング
        X = self.feature_engineer.create_advanced_features(X)
        
        # ラベル生成（実データがない場合は仮のラベル）
        if 'hit_label' in products.columns:
            y = products['hit_label'].values
        else:
            # 特徴量に基づいてラベルを生成（より現実的な分布）
            trend_score = X.get('trend_momentum', X.iloc[:, 0])
            threshold = trend_score.quantile(0.7)  # 上位30%をヒット
            y = (trend_score > threshold).astype(int).values
        
        logger.info(f"Prepared data: X shape={X.shape}, Hit ratio={y.mean():.1%}")
        
        return X, y
    
    def _generate_sample_products(self, n: int = 100) -> pd.DataFrame:
        """サンプル製品データを生成"""
        products = []
        
        ingredients = ['vitamin C', 'retinol', 'hyaluronic acid', 'niacinamide', 'peptides']
        categories = ['serum', 'cream', 'toner', 'mask', 'cleanser']
        
        for i in range(n):
            products.append({
                'product_id': f'PROD_{i:04d}',
                'name': f'{np.random.choice(categories).title()} with {np.random.choice(ingredients)}',
                'keywords': np.random.choice(ingredients, size=2).tolist(),
                'price': np.random.randint(2000, 30000),
                'brand_strength': np.random.uniform(0.2, 1.0),
                'ingredient_novelty': np.random.uniform(0.1, 1.0),
                'competitor_count': np.random.randint(5, 30),
                'market_saturation': np.random.uniform(0.2, 0.8)
            })
        
        return pd.DataFrame(products)
    
    def _extract_keywords(self, products: pd.DataFrame) -> list:
        """製品データからキーワードを抽出"""
        keywords = set()
        
        for _, product in products.iterrows():
            if 'keywords' in product:
                if isinstance(product['keywords'], list):
                    keywords.update(product['keywords'])
                else:
                    keywords.add(str(product['keywords']))
            
            if 'name' in product:
                # 製品名から単語を抽出
                words = str(product['name']).lower().split()
                keywords.update(words)
        
        return list(keywords)
    
    def optimize_hyperparameters(self, 
                                X: pd.DataFrame, 
                                y: np.ndarray,
                                cv: int = 5) -> Dict:
        """
        ハイパーパラメータを最適化（グリッドサーチ）
        
        Args:
            X: 特徴量
            y: ラベル
            cv: 交差検証の分割数
            
        Returns:
            最適パラメータ
        """
        logger.info("Starting hyperparameter optimization...")
        
        # パラメータグリッド
        param_grid = {
            'n_estimators': [50, 100, 200],
            'max_depth': [5, 10, 15, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4]
        }
        
        # グリッドサーチ
        from sklearn.ensemble import RandomForestClassifier
        base_model = RandomForestClassifier(random_state=42)
        
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=cv,
            scoring='f1',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        self.best_params = grid_search.best_params_
        logger.info(f"Best parameters: {self.best_params}")
        logger.info(f"Best CV score: {grid_search.best_score_:.3f}")
        
        return self.best_params
    
    def train_model(self, 
                   X: pd.DataFrame, 
                   y: np.ndarray,
                   optimize: bool = True) -> HitPredictionModel:
        """
        モデルを学習
        
        Args:
            X: 特徴量
            y: ラベル
            optimize: ハイパーパラメータを最適化するか
            
        Returns:
            学習済みモデル
        """
        logger.info("Training enhanced model...")
        
        # 特徴量を正規化
        X_normalized = self.feature_engineer.normalize_features(X.copy())
        
        # ハイパーパラメータ最適化
        if optimize:
            best_params = self.optimize_hyperparameters(X_normalized, y)
        else:
            best_params = {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 5,
                'min_samples_leaf': 2
            }
        
        # モデル初期化（最適パラメータを使用）
        self.model = HitPredictionModel()
        self.model.model.set_params(**best_params)
        
        # 学習
        metrics = self.model.train(X_normalized, y, validate=True)
        
        # 学習履歴を保存
        self.training_history.append({
            'timestamp': datetime.now().isoformat(),
            'params': best_params,
            'metrics': metrics,
            'feature_count': X.shape[1],
            'sample_count': X.shape[0]
        })
        
        return self.model
    
    def evaluate_model(self, 
                      X_test: pd.DataFrame, 
                      y_test: np.ndarray) -> Dict:
        """
        モデルを評価
        
        Args:
            X_test: テスト特徴量
            y_test: テストラベル
            
        Returns:
            評価メトリクス
        """
        if self.model is None:
            raise ValueError("Model not trained yet")
        
        logger.info("Evaluating model...")
        
        # 予測
        X_test_normalized = self.feature_engineer.normalize_features(X_test.copy())
        y_pred = (self.model.predict(X_test_normalized) >= 0.5).astype(int)
        
        # 分類レポート
        report = classification_report(y_test, y_pred, output_dict=True)
        
        # 混同行列
        cm = confusion_matrix(y_test, y_pred)
        
        # 詳細な評価結果
        evaluation = {
            'classification_report': report,
            'confusion_matrix': cm.tolist(),
            'accuracy': report['accuracy'],
            'precision': report['1']['precision'],
            'recall': report['1']['recall'],
            'f1_score': report['1']['f1-score']
        }
        
        # 結果を表示
        logger.info("\n=== Model Evaluation ===")
        logger.info(f"Accuracy: {evaluation['accuracy']:.3f}")
        logger.info(f"Precision: {evaluation['precision']:.3f}")
        logger.info(f"Recall: {evaluation['recall']:.3f}")
        logger.info(f"F1-Score: {evaluation['f1_score']:.3f}")
        logger.info(f"\nConfusion Matrix:")
        logger.info(f"  TN: {cm[0,0]}  FP: {cm[0,1]}")
        logger.info(f"  FN: {cm[1,0]}  TP: {cm[1,1]}")
        
        return evaluation
    
    def save_training_results(self, model_name: str = "enhanced_model_v2"):
        """
        学習結果を保存
        
        Args:
            model_name: モデル名
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # モデル保存
        model_path = self.model.save_model(f"{model_name}_{timestamp}.pkl")
        
        # 学習履歴保存
        history_path = os.path.join(self.model_dir, f"training_history_{timestamp}.json")
        with open(history_path, 'w') as f:
            json.dump(self.training_history, f, indent=2)
        
        # パラメータ保存
        if self.best_params:
            params_path = os.path.join(self.model_dir, f"best_params_{timestamp}.json")
            with open(params_path, 'w') as f:
                json.dump(self.best_params, f, indent=2)
        
        logger.info(f"Training results saved:")
        logger.info(f"  Model: {model_path}")
        logger.info(f"  History: {history_path}")
        
        return model_path
    
    def run_full_training_pipeline(self, 
                                  use_real_data: bool = False,
                                  optimize: bool = True):
        """
        完全な学習パイプラインを実行
        
        Args:
            use_real_data: 実データを使用するか
            optimize: ハイパーパラメータを最適化するか
        """
        logger.info("="*60)
        logger.info(" ENHANCED MODEL TRAINING PIPELINE ")
        logger.info("="*60)
        
        # 1. データ準備
        logger.info("\nStep 1: Preparing data...")
        X, y = self.prepare_data(use_real_data=use_real_data)
        
        # 2. 学習/テスト分割
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"Train set: {X_train.shape[0]} samples")
        logger.info(f"Test set: {X_test.shape[0]} samples")
        
        # 3. モデル学習
        logger.info("\nStep 2: Training model...")
        self.train_model(X_train, y_train, optimize=optimize)
        
        # 4. モデル評価
        logger.info("\nStep 3: Evaluating model...")
        evaluation = self.evaluate_model(X_test, y_test)
        
        # 5. 結果保存
        logger.info("\nStep 4: Saving results...")
        model_path = self.save_training_results()
        
        # 6. サマリー表示
        logger.info("\n" + "="*60)
        logger.info(" TRAINING COMPLETED ")
        logger.info("="*60)
        logger.info(f"Final F1-Score: {evaluation['f1_score']:.3f}")
        logger.info(f"Model saved to: {model_path}")
        
        return self.model, evaluation


def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Train enhanced hit prediction model')
    parser.add_argument('--real-data', action='store_true', help='Use real API data')
    parser.add_argument('--no-optimize', action='store_true', help='Skip hyperparameter optimization')
    parser.add_argument('--products-file', type=str, help='Path to products CSV file')
    
    args = parser.parse_args()
    
    # トレーナー初期化
    trainer = EnhancedModelTrainer()
    
    # 学習実行
    model, evaluation = trainer.run_full_training_pipeline(
        use_real_data=args.real_data,
        optimize=not args.no_optimize
    )
    
    logger.info("\n✅ Training pipeline completed successfully!")
    
    return model, evaluation


if __name__ == "__main__":
    # 実行
    model, evaluation = main()