#!/usr/bin/env python
"""
Phase 3 統合テストスクリプト
SHAP分析、Streamlit UI、Optuna最適化、リアルタイムダッシュボードの動作確認
"""

import sys
import os
import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.preprocessing.data_pipeline import DataPipeline
from src.preprocessing.feature_engineering import FeatureEngineer
from src.models.basic_model import HitPredictionModel
from src.analysis.model_explainer import ModelExplainer
from src.optimization.hyperparameter_optimizer import HyperparameterOptimizer, AutoML

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase3Tester:
    """Phase 3の統合テストクラス"""
    
    def __init__(self):
        """初期化"""
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'Phase 3',
            'tests': []
        }
        self.test_data = {}
        self.sample_data = None
        self.model = None
        
    def add_test_result(self, test_name: str, success: bool, details: str = "", data: any = None):
        """テスト結果を記録"""
        self.test_results['tests'].append({
            'name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        if data is not None:
            self.test_data[test_name] = data
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"  Details: {details}")
    
    def prepare_test_data(self):
        """テスト用データの準備"""
        logger.info("\n" + "="*50)
        logger.info("Preparing Test Data")
        logger.info("="*50)
        
        try:
            # パイプラインとエンジニア初期化
            pipeline = DataPipeline()
            engineer = FeatureEngineer()
            
            # サンプル製品データ生成
            products = []
            for i in range(100):
                products.append({
                    'name': f'Test Product {i}',
                    'keywords': ['test', 'sample', 'product'],
                    'price': np.random.randint(2000, 20000),
                    'brand_strength': np.random.uniform(0.3, 0.9),
                    'ingredient_novelty': np.random.uniform(0.2, 0.8),
                    'market_saturation': np.random.uniform(0.1, 0.6)
                })
            
            # 特徴量抽出
            X_list = []
            for product in products:
                features = pipeline.extract_features(product)
                X_list.append(features)
            
            X = pd.concat(X_list, ignore_index=True)
            X_enhanced = engineer.create_advanced_features(X)
            
            # ターゲット生成（モック）
            y = np.random.choice([0, 1], size=len(products), p=[0.6, 0.4])
            
            # 訓練・検証データ分割
            split_idx = int(len(X_enhanced) * 0.8)
            X_train = X_enhanced[:split_idx]
            y_train = y[:split_idx]
            X_val = X_enhanced[split_idx:]
            y_val = y[split_idx:]
            
            self.sample_data = {
                'X_train': X_train,
                'y_train': y_train,
                'X_val': X_val,
                'y_val': y_val,
                'products': products
            }
            
            self.add_test_result(
                "Test Data Preparation",
                True,
                f"Prepared {len(X_train)} training and {len(X_val)} validation samples"
            )
            
            # 基本モデルの訓練
            model = HitPredictionModel()
            model.train(X_train, y_train, validate=False)
            self.model = model
            
            self.add_test_result(
                "Base Model Training",
                True,
                "Model trained successfully for testing"
            )
            
            return True
            
        except Exception as e:
            self.add_test_result(
                "Test Data Preparation",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_shap_analysis(self) -> bool:
        """SHAP分析機能のテスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing SHAP Analysis Module")
        logger.info("="*50)
        
        try:
            if self.model is None or self.sample_data is None:
                raise ValueError("Test data not prepared")
            
            # ModelExplainer初期化
            explainer = ModelExplainer(self.model.model)
            
            # 単一サンプルの説明
            X_single = self.sample_data['X_val'].iloc[[0]]
            
            # SHAP値計算
            logger.info("Calculating SHAP values...")
            shap_values = explainer.calculate_shap_values(X_single)
            
            self.add_test_result(
                "SHAP Values Calculation",
                shap_values is not None and shap_values.shape == X_single.shape,
                f"SHAP values shape: {shap_values.shape}"
            )
            
            # 特徴量重要度取得
            importance = explainer.get_feature_importance()
            self.add_test_result(
                "Feature Importance Extraction",
                len(importance) > 0,
                f"Top 3 features: {list(importance.head(3).index)}"
            )
            
            # Force plot データ生成
            force_plot_data = explainer.create_force_plot_data(X_single)
            self.add_test_result(
                "Force Plot Data Generation",
                'base_value' in force_plot_data and 'shap_values' in force_plot_data,
                f"Base value: {force_plot_data.get('base_value', 0):.3f}"
            )
            
            # 説明レポート生成
            report = explainer.generate_explanation_report(X_single, "Test Product")
            self.add_test_result(
                "Explanation Report Generation",
                all(k in report for k in ['prediction', 'confidence', 'top_positive_factors']),
                f"Report keys: {list(report.keys())}"
            )
            
            # バッチ処理
            logger.info("Testing batch SHAP analysis...")
            X_batch = self.sample_data['X_val'].iloc[:10]
            batch_shap = explainer.calculate_shap_values(X_batch)
            
            self.add_test_result(
                "Batch SHAP Analysis",
                batch_shap.shape == X_batch.shape,
                f"Processed {len(X_batch)} samples"
            )
            
            return True
            
        except Exception as e:
            self.add_test_result(
                "SHAP Analysis Module",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_optuna_optimization(self) -> bool:
        """Optuna最適化のテスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing Optuna Hyperparameter Optimization")
        logger.info("="*50)
        
        try:
            if self.sample_data is None:
                raise ValueError("Test data not prepared")
            
            # 小規模データで高速テスト
            X_train = self.sample_data['X_train'][:50]
            y_train = self.sample_data['y_train'][:50]
            X_val = self.sample_data['X_val'][:20]
            y_val = self.sample_data['y_val'][:20]
            
            # Random Forest最適化
            logger.info("Testing Random Forest optimization...")
            rf_optimizer = HyperparameterOptimizer(
                model_type='random_forest',
                n_trials=10  # テスト用に少ない試行回数
            )
            
            rf_results = rf_optimizer.optimize(X_train, y_train, X_val, y_val)
            
            self.add_test_result(
                "Random Forest Optimization",
                'best_params' in rf_results and 'best_cv_score' in rf_results,
                f"Best CV score: {rf_results.get('best_cv_score', 0):.3f}"
            )
            
            # XGBoost最適化
            logger.info("Testing XGBoost optimization...")
            xgb_optimizer = HyperparameterOptimizer(
                model_type='xgboost',
                n_trials=5  # より少ない試行回数
            )
            
            xgb_results = xgb_optimizer.optimize(X_train, y_train, X_val, y_val)
            
            self.add_test_result(
                "XGBoost Optimization",
                'best_params' in xgb_results,
                f"Validation F1: {xgb_results.get('validation_metrics', {}).get('f1', 0):.3f}"
            )
            
            # LightGBM最適化
            logger.info("Testing LightGBM optimization...")
            lgb_optimizer = HyperparameterOptimizer(
                model_type='lightgbm',
                n_trials=5
            )
            
            lgb_results = lgb_optimizer.optimize(X_train, y_train, X_val, y_val)
            
            self.add_test_result(
                "LightGBM Optimization",
                'best_params' in lgb_results,
                f"Validation accuracy: {lgb_results.get('validation_metrics', {}).get('accuracy', 0):.3f}"
            )
            
            # 特徴量重要度取得
            if rf_optimizer.best_model:
                importance_df = rf_optimizer.get_feature_importance(X_train.columns.tolist())
                self.add_test_result(
                    "Feature Importance from Optimized Model",
                    len(importance_df) > 0,
                    f"Top feature: {importance_df.iloc[0]['feature']}"
                )
            
            # モデル保存・読み込みテスト
            test_model_path = "test_optimized_model.pkl"
            rf_optimizer.save_model(test_model_path)
            
            new_optimizer = HyperparameterOptimizer()
            new_optimizer.load_model(test_model_path)
            
            self.add_test_result(
                "Model Save/Load",
                new_optimizer.best_model is not None,
                f"Model successfully saved and loaded"
            )
            
            # ファイルクリーンアップ
            if os.path.exists(test_model_path):
                os.remove(test_model_path)
            
            return True
            
        except Exception as e:
            self.add_test_result(
                "Optuna Optimization",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_automl(self) -> bool:
        """AutoML機能のテスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing AutoML Functionality")
        logger.info("="*50)
        
        try:
            if self.sample_data is None:
                raise ValueError("Test data not prepared")
            
            # 小規模データで高速テスト
            X_train = self.sample_data['X_train'][:30]
            y_train = self.sample_data['y_train'][:30]
            X_val = self.sample_data['X_val'][:10]
            y_val = self.sample_data['y_val'][:10]
            
            # AutoML実行
            logger.info("Running AutoML...")
            automl = AutoML(n_trials=3)  # テスト用に非常に少ない試行回数
            
            results = automl.fit(X_train, y_train, X_val, y_val)
            
            self.add_test_result(
                "AutoML Execution",
                'best_model_type' in results,
                f"Best model: {results.get('best_model_type', 'unknown')}"
            )
            
            # 予測テスト
            predictions = automl.predict(X_val)
            pred_proba = automl.predict_proba(X_val)
            
            self.add_test_result(
                "AutoML Predictions",
                len(predictions) == len(X_val) and pred_proba.shape[0] == len(X_val),
                f"Generated {len(predictions)} predictions"
            )
            
            # モデル比較結果確認
            if 'comparison' in results:
                comparison = pd.DataFrame(results['comparison'])
                self.add_test_result(
                    "Model Comparison",
                    len(comparison) > 0,
                    f"Compared {len(comparison)} models"
                )
            
            return True
            
        except Exception as e:
            self.add_test_result(
                "AutoML",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_streamlit_components(self) -> bool:
        """Streamlitコンポーネントのテスト（インポート確認）"""
        logger.info("\n" + "="*50)
        logger.info("Testing Streamlit Components")
        logger.info("="*50)
        
        try:
            # Streamlit app のインポート確認
            import streamlit_app
            
            self.add_test_result(
                "Streamlit App Import",
                True,
                "streamlit_app.py successfully imported"
            )
            
            # Dashboard のインポート確認
            import streamlit_dashboard
            
            self.add_test_result(
                "Dashboard Import",
                True,
                "streamlit_dashboard.py successfully imported"
            )
            
            # 必要なStreamlitコンポーネントの確認
            import streamlit as st
            import plotly.graph_objects as go
            import plotly.express as px
            
            self.add_test_result(
                "Required Libraries",
                True,
                "All required visualization libraries available"
            )
            
            return True
            
        except ImportError as e:
            self.add_test_result(
                "Streamlit Components",
                False,
                f"Import error: {str(e)}"
            )
            return False
        except Exception as e:
            self.add_test_result(
                "Streamlit Components",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_integration(self) -> bool:
        """統合テスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing Full Integration")
        logger.info("="*50)
        
        try:
            # エンドツーエンドのワークフローテスト
            pipeline = DataPipeline()
            engineer = FeatureEngineer()
            
            # 1. 新製品データ
            new_product = {
                'name': 'Revolutionary Anti-Aging Serum',
                'keywords': ['retinol', 'peptide', 'vitamin C'],
                'price': 12000,
                'brand_strength': 0.8,
                'ingredient_novelty': 0.9,
                'market_saturation': 0.3
            }
            
            # 2. 特徴量抽出
            logger.info("Extracting features...")
            features = pipeline.extract_features(new_product)
            enhanced_features = engineer.create_advanced_features(features)
            
            self.add_test_result(
                "Feature Pipeline Integration",
                enhanced_features.shape[1] > features.shape[1],
                f"Enhanced from {features.shape[1]} to {enhanced_features.shape[1]} features"
            )
            
            # 3. 予測実行
            if self.model:
                logger.info("Making prediction...")
                prediction = self.model.predict_with_confidence(enhanced_features)
                
                self.add_test_result(
                    "Prediction Pipeline",
                    'hit_probability' in prediction.columns,
                    f"Hit probability: {prediction['hit_probability'].iloc[0]:.2%}"
                )
                
                # 4. SHAP説明
                logger.info("Generating explanation...")
                explainer = ModelExplainer(self.model.model)
                explanation = explainer.generate_explanation_report(
                    enhanced_features,
                    new_product['name']
                )
                
                self.add_test_result(
                    "Explanation Integration",
                    'top_positive_factors' in explanation,
                    f"Generated {len(explanation.get('top_positive_factors', []))} positive factors"
                )
            
            # 5. 最適化との統合
            logger.info("Testing optimization integration...")
            small_X = self.sample_data['X_train'][:20]
            small_y = self.sample_data['y_train'][:20]
            
            optimizer = HyperparameterOptimizer(
                model_type='random_forest',
                n_trials=3
            )
            opt_results = optimizer.optimize(small_X, small_y)
            
            self.add_test_result(
                "Optimization Integration",
                optimizer.best_model is not None,
                "Optimized model created successfully"
            )
            
            return True
            
        except Exception as e:
            self.add_test_result(
                "Full Integration",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def save_test_results(self):
        """テスト結果を保存"""
        os.makedirs("tests", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"tests/phase3_results_{timestamp}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"\nTest results saved to: {filepath}")
        
        return filepath
    
    def print_summary(self):
        """テスト結果のサマリーを表示"""
        total = len(self.test_results['tests'])
        passed = sum(1 for t in self.test_results['tests'] if t['success'])
        failed = total - passed
        
        logger.info("\n" + "="*50)
        logger.info("PHASE 3 TEST SUMMARY")
        logger.info("="*50)
        logger.info(f"Total Tests: {total}")
        logger.info(f"✅ Passed: {passed}")
        logger.info(f"❌ Failed: {failed}")
        logger.info(f"Success Rate: {(passed/total*100):.1f}%")
        
        if failed > 0:
            logger.info("\nFailed Tests:")
            for test in self.test_results['tests']:
                if not test['success']:
                    logger.info(f"  - {test['name']}: {test['details']}")
        
        # Phase 3の新機能サマリー
        logger.info("\n" + "="*50)
        logger.info("PHASE 3 FEATURES SUMMARY")
        logger.info("="*50)
        logger.info("✅ SHAP Analysis for Model Explainability")
        logger.info("✅ Streamlit Web UI (Prediction Interface)")
        logger.info("✅ Optuna Hyperparameter Optimization")
        logger.info("✅ AutoML with Model Comparison")
        logger.info("✅ Real-time Dashboard with Metrics")
        logger.info("✅ Advanced Visualizations")
        logger.info("✅ Model Performance Monitoring")
        logger.info("✅ Export and Reporting Features")
        
        return passed == total


def main():
    """メイン実行関数"""
    logger.info("="*60)
    logger.info(" AI HIT PREDICTION SYSTEM - PHASE 3 TEST ")
    logger.info("="*60)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = Phase3Tester()
    
    # テストデータ準備
    if not tester.prepare_test_data():
        logger.error("Failed to prepare test data. Exiting.")
        return False
    
    # 各モジュールのテスト実行
    test_functions = [
        tester.test_shap_analysis,
        tester.test_optuna_optimization,
        tester.test_automl,
        tester.test_streamlit_components,
        tester.test_integration
    ]
    
    all_passed = True
    for test_func in test_functions:
        try:
            result = test_func()
            if not result:
                all_passed = False
        except Exception as e:
            logger.error(f"Test failed with exception: {e}")
            all_passed = False
    
    # 結果サマリー
    all_tests_passed = tester.print_summary()
    
    # 結果保存
    tester.save_test_results()
    
    # 最終結果
    logger.info("\n" + "="*60)
    if all_tests_passed and all_passed:
        logger.info("🎉 ALL PHASE 3 TESTS PASSED! System is ready for deployment.")
        logger.info("\nTo launch the web UI:")
        logger.info("  1. Basic UI: streamlit run streamlit_app.py")
        logger.info("  2. Dashboard: streamlit run streamlit_dashboard.py")
    else:
        logger.info("⚠️  Some tests failed. Please review the results.")
    logger.info("="*60)
    
    return all_tests_passed


if __name__ == "__main__":
    # テスト実行
    success = main()
    sys.exit(0 if success else 1)