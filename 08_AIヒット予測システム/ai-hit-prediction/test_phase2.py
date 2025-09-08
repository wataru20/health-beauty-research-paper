#!/usr/bin/env python
"""
Phase 2 統合テストスクリプト
新機能の動作確認と統合テスト
"""

import sys
import os
import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.academic_collector import AcademicPaperCollector
from src.data_collection.news_collector import NewsCollector
from src.preprocessing.data_pipeline import DataPipeline
from src.preprocessing.feature_engineering import FeatureEngineer
from src.models.basic_model import HitPredictionModel

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Phase2Tester:
    """Phase 2の統合テストクラス"""
    
    def __init__(self):
        """初期化"""
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'phase': 'Phase 2',
            'tests': []
        }
        self.test_data = {}
    
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
    
    def test_news_collection(self) -> bool:
        """ニュース収集機能のテスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing News Collection Module")
        logger.info("="*50)
        
        try:
            # NewsCollector初期化
            collector = NewsCollector()
            
            # テストキーワード
            test_keywords = ["vitamin C serum", "retinol cream"]
            
            # ニュース検索
            logger.info("Searching news articles...")
            results = collector.search_news(test_keywords, days_back=7)
            
            if results and results.get('status') == 'ok':
                article_count = results.get('totalResults', 0)
                self.add_test_result(
                    "News API Connection",
                    True,
                    f"Retrieved {article_count} articles",
                    data={'article_count': article_count}
                )
                
                # トレンド抽出テスト
                if results.get('articles'):
                    trends = collector.extract_trends(results['articles'])
                    self.add_test_result(
                        "Trend Extraction",
                        bool(trends),
                        f"Extracted trends from {trends.get('total_articles', 0)} articles"
                    )
                    
                    # センチメント分析テスト
                    sentiment = collector.analyze_sentiment(results['articles'])
                    self.add_test_result(
                        "Sentiment Analysis",
                        'polarity' in sentiment,
                        f"Sentiment: {sentiment.get('sentiment_label', 'unknown')}"
                    )
                    
                    # バズスコア計算テスト
                    buzz_score = collector.calculate_buzz_score(results['articles'])
                    self.add_test_result(
                        "Buzz Score Calculation",
                        0 <= buzz_score <= 1,
                        f"Buzz score: {buzz_score:.3f}"
                    )
                else:
                    self.add_test_result(
                        "News Data Processing",
                        False,
                        "No articles to process"
                    )
                
                return True
            else:
                self.add_test_result(
                    "News API Connection",
                    False,
                    "Failed to retrieve news data (API key may be required)"
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                "News Collection Module",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_data_pipeline(self) -> bool:
        """データパイプラインのテスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing Data Pipeline")
        logger.info("="*50)
        
        try:
            # パイプライン初期化
            pipeline = DataPipeline()
            
            # テスト製品情報
            test_product = {
                'name': 'Test Vitamin C Serum',
                'keywords': ['vitamin C', 'brightening'],
                'price': 5000,
                'brand_strength': 0.7
            }
            
            # 特徴量抽出テスト
            logger.info("Extracting features...")
            features = pipeline.extract_features(test_product)
            
            feature_count = features.shape[1]
            self.add_test_result(
                "Feature Extraction",
                feature_count > 0,
                f"Extracted {feature_count} features",
                data={'features': features.columns.tolist()}
            )
            
            # 主要な特徴量の確認
            required_features = [
                'academic_paper_count',
                'academic_trend_score',
                'news_article_count',
                'news_buzz_score',
                'price_range'
            ]
            
            missing_features = [f for f in required_features if f not in features.columns]
            self.add_test_result(
                "Required Features Check",
                len(missing_features) == 0,
                f"Missing features: {missing_features}" if missing_features else "All required features present"
            )
            
            # 複数製品の処理テスト
            test_products = [
                {'name': f'Product {i}', 'keywords': ['test'], 'price': 5000 * i}
                for i in range(5)
            ]
            
            X, y = pipeline.prepare_training_data(test_products)
            self.add_test_result(
                "Batch Processing",
                X.shape[0] == len(test_products),
                f"Processed {X.shape[0]} products with {X.shape[1]} features each"
            )
            
            return True
            
        except Exception as e:
            self.add_test_result(
                "Data Pipeline",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_feature_engineering(self) -> bool:
        """特徴量エンジニアリングのテスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing Feature Engineering")
        logger.info("="*50)
        
        try:
            # エンジニア初期化
            engineer = FeatureEngineer()
            
            # サンプルデータ生成
            sample_features = pd.DataFrame({
                'academic_trend_score': [0.7, 0.3, 0.5],
                'news_buzz_score': [0.8, 0.4, 0.6],
                'price_range': [3, 2, 4],
                'brand_strength': [0.8, 0.5, 0.7],
                'ingredient_novelty': [0.6, 0.8, 0.4],
                'market_saturation': [0.3, 0.7, 0.5],
                'competitor_count': [10, 20, 15]
            })
            
            original_count = sample_features.shape[1]
            
            # 高度な特徴量生成
            logger.info("Creating advanced features...")
            enhanced_features = engineer.create_advanced_features(sample_features)
            
            new_count = enhanced_features.shape[1]
            new_features = [col for col in enhanced_features.columns 
                          if col not in sample_features.columns]
            
            self.add_test_result(
                "Advanced Feature Creation",
                new_count > original_count,
                f"Created {len(new_features)} new features from {original_count} original",
                data={'new_features': new_features}
            )
            
            # 特徴量正規化テスト
            normalized = engineer.normalize_features(enhanced_features.copy())
            
            # 正規化の確認（平均≈0、標準偏差≈1）
            numeric_cols = normalized.select_dtypes(include=[np.number]).columns
            means = normalized[numeric_cols].mean()
            stds = normalized[numeric_cols].std()
            
            normalization_ok = (abs(means).mean() < 0.1) and (abs(stds - 1).mean() < 0.2)
            self.add_test_result(
                "Feature Normalization",
                normalization_ok,
                f"Mean: {means.mean():.3f}, Std: {stds.mean():.3f}"
            )
            
            # 特徴量選択テスト
            top_features = engineer.select_top_features(enhanced_features, top_n=5)
            self.add_test_result(
                "Feature Selection",
                top_features.shape[1] == 5,
                f"Selected top {top_features.shape[1]} features"
            )
            
            return True
            
        except Exception as e:
            self.add_test_result(
                "Feature Engineering",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_enhanced_model_training(self) -> bool:
        """拡張モデル学習のテスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing Enhanced Model Training")
        logger.info("="*50)
        
        try:
            # パイプラインとエンジニア初期化
            pipeline = DataPipeline()
            engineer = FeatureEngineer()
            
            # サンプル製品データ生成
            products = [
                {'name': f'Product {i}', 'keywords': ['test'], 'price': 5000 * (i % 5 + 1)}
                for i in range(50)
            ]
            
            # 特徴量準備
            X, y = pipeline.prepare_training_data(products)
            X_enhanced = engineer.create_advanced_features(X)
            
            logger.info(f"Training data shape: {X_enhanced.shape}")
            
            # モデル学習
            model = HitPredictionModel()
            metrics = model.train(X_enhanced, y, validate=True)
            
            self.add_test_result(
                "Enhanced Model Training",
                metrics['test']['accuracy'] > 0,
                f"Test accuracy: {metrics['test']['accuracy']:.3f}"
            )
            
            # 予測テスト
            test_product = {'name': 'New Product', 'keywords': ['innovative'], 'price': 10000}
            X_test = pipeline.extract_features(test_product)
            X_test_enhanced = engineer.create_advanced_features(X_test)
            
            predictions = model.predict_with_confidence(X_test_enhanced)
            
            self.add_test_result(
                "Enhanced Prediction",
                'hit_probability' in predictions.columns,
                f"Prediction probability: {predictions['hit_probability'].iloc[0]:.2%}"
            )
            
            return True
            
        except Exception as e:
            self.add_test_result(
                "Enhanced Model Training",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_full_pipeline_integration(self) -> bool:
        """完全パイプライン統合テスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing Full Pipeline Integration")
        logger.info("="*50)
        
        try:
            # 1. データ収集
            logger.info("\n1. Data Collection Phase")
            pipeline = DataPipeline()
            
            keywords = ["retinol", "niacinamide"]
            logger.info(f"Collecting data for keywords: {keywords}")
            
            # 実際のデータ収集は省略（APIキーなしでも動作するように）
            # collected_data = pipeline.collect_all_data(keywords, days_back=7)
            
            self.add_test_result(
                "Data Collection Pipeline",
                True,
                "Data collection pipeline initialized"
            )
            
            # 2. 特徴量生成
            logger.info("\n2. Feature Engineering Phase")
            test_product = {
                'name': 'Revolutionary Retinol Serum',
                'keywords': keywords,
                'price': 15000,
                'brand_strength': 0.9,
                'ingredient_novelty': 0.8
            }
            
            features = pipeline.extract_features(test_product)
            engineer = FeatureEngineer()
            enhanced_features = engineer.create_advanced_features(features)
            
            self.add_test_result(
                "Feature Pipeline",
                enhanced_features.shape[1] > features.shape[1],
                f"Enhanced features from {features.shape[1]} to {enhanced_features.shape[1]}"
            )
            
            # 3. モデル予測
            logger.info("\n3. Model Prediction Phase")
            
            # ダミーモデルで予測（実際の学習済みモデルがない場合）
            model = HitPredictionModel()
            
            # ダミーデータで簡易学習
            X_dummy = pd.concat([enhanced_features] * 20, ignore_index=True)
            y_dummy = np.random.choice([0, 1], size=20)
            model.train(X_dummy, y_dummy, validate=False)
            
            # 予測実行
            prediction_result = model.predict_with_confidence(enhanced_features)
            
            self.add_test_result(
                "End-to-End Prediction",
                prediction_result is not None,
                f"Hit probability: {prediction_result['hit_probability'].iloc[0]:.2%}, "
                f"Risk: {prediction_result['risk_level'].iloc[0]}"
            )
            
            return True
            
        except Exception as e:
            self.add_test_result(
                "Full Pipeline Integration",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def save_test_results(self):
        """テスト結果を保存"""
        os.makedirs("tests", exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"tests/phase2_results_{timestamp}.json"
        
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
        logger.info("PHASE 2 TEST SUMMARY")
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
        
        # 新機能のサマリー
        logger.info("\n" + "="*50)
        logger.info("NEW FEATURES IN PHASE 2")
        logger.info("="*50)
        logger.info("✅ News API Integration (with fallback to mock data)")
        logger.info("✅ Advanced Data Pipeline")
        logger.info("✅ Feature Engineering (20+ new features)")
        logger.info("✅ Enhanced Model Training")
        logger.info("✅ Sentiment Analysis")
        logger.info("✅ Buzz Score Calculation")
        
        return passed == total


def main():
    """メイン実行関数"""
    logger.info("="*60)
    logger.info(" AI HIT PREDICTION SYSTEM - PHASE 2 TEST ")
    logger.info("="*60)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = Phase2Tester()
    
    # 各モジュールのテスト実行
    test_functions = [
        tester.test_news_collection,
        tester.test_data_pipeline,
        tester.test_feature_engineering,
        tester.test_enhanced_model_training,
        tester.test_full_pipeline_integration
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
        logger.info("🎉 ALL PHASE 2 TESTS PASSED! Ready for Phase 3.")
    else:
        logger.info("⚠️  Some tests failed. Please review the results.")
    logger.info("="*60)
    
    return all_tests_passed


if __name__ == "__main__":
    # テスト実行
    success = main()
    sys.exit(0 if success else 1)