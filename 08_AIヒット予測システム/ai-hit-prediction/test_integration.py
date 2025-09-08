#!/usr/bin/env python
"""
統合テストスクリプト
Phase 1の全コンポーネントが正しく動作することを確認
"""

import sys
import os
import logging
import json
import pandas as pd
import numpy as np
from datetime import datetime

# プロジェクトのルートをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.academic_collector import AcademicPaperCollector
from src.models.basic_model import HitPredictionModel, generate_dummy_data

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IntegrationTest:
    """統合テストクラス"""
    
    def __init__(self):
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': []
        }
    
    def add_test_result(self, test_name: str, success: bool, details: str = ""):
        """テスト結果を記録"""
        self.test_results['tests'].append({
            'name': test_name,
            'success': success,
            'details': details
        })
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if details:
            logger.info(f"  Details: {details}")
    
    def test_data_collection(self) -> bool:
        """データ収集モジュールのテスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing Data Collection Module")
        logger.info("="*50)
        
        try:
            # コレクター初期化
            collector = AcademicPaperCollector()
            
            # 単一キーワードでテスト
            test_keyword = "vitamin C"
            logger.info(f"Testing search with keyword: '{test_keyword}'")
            
            papers = collector.search_papers(test_keyword, limit=3)
            
            if papers and 'data' in papers:
                paper_count = len(papers['data'])
                self.add_test_result(
                    "Academic API Connection",
                    True,
                    f"Retrieved {paper_count} papers"
                )
                
                # メトリクス抽出テスト
                metrics = collector.extract_trend_metrics(papers['data'])
                self.add_test_result(
                    "Metrics Extraction",
                    metrics['total_papers'] > 0,
                    f"Calculated metrics for {metrics['total_papers']} papers"
                )
                
                # ファイル保存テスト
                test_data = {'test_keyword': papers['data']}
                filepath = collector.save_to_file(test_data, prefix="test_papers")
                
                self.add_test_result(
                    "Data Save to File",
                    os.path.exists(filepath),
                    f"Saved to {filepath}"
                )
                
                # ファイル読み込みテスト
                loaded_data = collector.load_from_file(filepath)
                self.add_test_result(
                    "Data Load from File",
                    loaded_data is not None,
                    f"Loaded {len(loaded_data.get('test_keyword', []))} papers"
                )
                
                return True
            else:
                self.add_test_result(
                    "Academic API Connection",
                    False,
                    "No data retrieved from API"
                )
                return False
                
        except Exception as e:
            self.add_test_result(
                "Data Collection Module",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_model_training(self) -> bool:
        """モデル学習モジュールのテスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing Model Training Module")
        logger.info("="*50)
        
        try:
            # モデル初期化
            model = HitPredictionModel()
            self.add_test_result(
                "Model Initialization",
                True,
                "HitPredictionModel initialized"
            )
            
            # ダミーデータ生成
            data, labels = generate_dummy_data(n_samples=100)
            self.add_test_result(
                "Dummy Data Generation",
                len(data) == 100,
                f"Generated {len(data)} samples"
            )
            
            # 特徴量準備
            X = model.prepare_features(data)
            self.add_test_result(
                "Feature Preparation",
                X.shape[1] == 12,  # 12個の特徴量
                f"Prepared {X.shape[1]} features"
            )
            
            # モデル学習
            metrics = model.train(X, labels, validate=False)
            test_accuracy = metrics['test']['accuracy']
            
            self.add_test_result(
                "Model Training",
                test_accuracy > 0.5,  # 最低限のパフォーマンス
                f"Test accuracy: {test_accuracy:.3f}"
            )
            
            # 予測テスト
            new_data = pd.DataFrame({
                'product_id': ['TEST_001'],
                'product_name': ['Test Product']
            })
            X_new = model.prepare_features(new_data)
            predictions = model.predict_with_confidence(X_new)
            
            self.add_test_result(
                "Prediction Generation",
                len(predictions) == 1,
                f"Hit probability: {predictions.iloc[0]['hit_probability']:.1%}"
            )
            
            # モデル保存
            model_path = model.save_model("test_model.pkl")
            self.add_test_result(
                "Model Save",
                os.path.exists(model_path),
                f"Saved to {model_path}"
            )
            
            # モデル読み込み
            new_model = HitPredictionModel()
            new_model.load_model(model_path)
            
            self.add_test_result(
                "Model Load",
                new_model.is_trained,
                "Model loaded successfully"
            )
            
            return True
            
        except Exception as e:
            self.add_test_result(
                "Model Training Module",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def test_full_pipeline(self) -> bool:
        """完全なパイプラインのテスト"""
        logger.info("\n" + "="*50)
        logger.info("Testing Full Pipeline Integration")
        logger.info("="*50)
        
        try:
            # Step 1: データ収集
            logger.info("\nStep 1: Collecting academic data...")
            collector = AcademicPaperCollector()
            
            keywords = ["retinol", "hyaluronic acid"]
            results = collector.collect_papers_for_keywords(keywords, papers_per_keyword=2)
            
            total_papers = sum(len(papers) for papers in results.values())
            self.add_test_result(
                "Pipeline: Data Collection",
                total_papers > 0,
                f"Collected {total_papers} papers for {len(keywords)} keywords"
            )
            
            # Step 2: データ処理（簡易版）
            logger.info("\nStep 2: Processing data...")
            trend_scores = {}
            for keyword, papers in results.items():
                metrics = collector.extract_trend_metrics(papers)
                trend_scores[keyword] = metrics['avg_citations']
            
            self.add_test_result(
                "Pipeline: Data Processing",
                len(trend_scores) == len(keywords),
                f"Calculated trend scores for {len(trend_scores)} keywords"
            )
            
            # Step 3: モデル学習
            logger.info("\nStep 3: Training model...")
            model = HitPredictionModel()
            
            # 仮の製品データを作成
            products = pd.DataFrame({
                'product_id': [f'PROD_{i:03d}' for i in range(50)],
                'product_name': [f'Product with {kw}' for kw in keywords * 25]
            })
            
            X = model.prepare_features(products)
            y = np.random.choice([0, 1], size=len(products), p=[0.6, 0.4])
            
            metrics = model.train(X, y, validate=False)
            
            self.add_test_result(
                "Pipeline: Model Training",
                metrics['test']['accuracy'] > 0,
                f"Model trained with accuracy: {metrics['test']['accuracy']:.3f}"
            )
            
            # Step 4: 新商品予測
            logger.info("\nStep 4: Making predictions...")
            new_product = pd.DataFrame({
                'product_id': ['NEW_SERUM_001'],
                'product_name': ['Revolutionary Retinol Serum']
            })
            
            X_new = model.prepare_features(new_product)
            prediction = model.predict_with_confidence(X_new)
            
            hit_prob = prediction.iloc[0]['hit_probability']
            risk_level = prediction.iloc[0]['risk_level']
            
            self.add_test_result(
                "Pipeline: Prediction",
                True,
                f"Prediction complete - Hit: {hit_prob:.1%}, Risk: {risk_level}"
            )
            
            return True
            
        except Exception as e:
            self.add_test_result(
                "Full Pipeline",
                False,
                f"Error: {str(e)}"
            )
            return False
    
    def save_test_results(self):
        """テスト結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"tests/test_results_{timestamp}.json"
        
        os.makedirs("tests", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"\nTest results saved to: {filepath}")
    
    def print_summary(self):
        """テスト結果のサマリーを表示"""
        total = len(self.test_results['tests'])
        passed = sum(1 for t in self.test_results['tests'] if t['success'])
        failed = total - passed
        
        logger.info("\n" + "="*50)
        logger.info("TEST SUMMARY")
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
        
        return passed == total


def main():
    """メイン実行関数"""
    logger.info("="*60)
    logger.info(" AI HIT PREDICTION SYSTEM - INTEGRATION TEST ")
    logger.info("="*60)
    logger.info(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = IntegrationTest()
    
    # 各モジュールのテスト
    all_success = True
    
    # データ収集テスト
    if not tester.test_data_collection():
        logger.warning("⚠️  Data collection test failed - using offline mode")
        # APIが利用できない場合も継続
    
    # モデルテスト
    if not tester.test_model_training():
        all_success = False
    
    # 統合テスト
    if not tester.test_full_pipeline():
        logger.warning("⚠️  Pipeline test failed - some components may not be integrated")
    
    # 結果サマリー
    all_tests_passed = tester.print_summary()
    
    # 結果保存
    tester.save_test_results()
    
    # 最終結果
    logger.info("\n" + "="*60)
    if all_tests_passed:
        logger.info("🎉 ALL TESTS PASSED! System is ready for Phase 1.")
    else:
        logger.warning("⚠️  Some tests failed. Please review the results.")
    logger.info("="*60)
    
    return all_tests_passed


if __name__ == "__main__":
    # テスト実行
    success = main()
    sys.exit(0 if success else 1)