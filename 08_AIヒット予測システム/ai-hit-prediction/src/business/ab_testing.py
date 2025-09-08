#!/usr/bin/env python
"""
A/B Testing Support Module
A/Bテスト支援機能
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import scipy.stats as stats
from scipy.stats import chi2_contingency, ttest_ind, mannwhitneyu
import json
import logging
from dataclasses import dataclass
from enum import Enum

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestStatus(Enum):
    """テストステータス"""
    PLANNING = "planning"
    RUNNING = "running"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


@dataclass
class ABTestConfig:
    """A/Bテスト設定"""
    test_name: str
    variant_a: Dict[str, Any]  # コントロール群
    variant_b: Dict[str, Any]  # テスト群
    sample_size: int
    confidence_level: float = 0.95
    power: float = 0.8
    minimum_detectable_effect: float = 0.05
    test_duration_days: int = 14
    primary_metric: str = "conversion_rate"
    secondary_metrics: List[str] = None


class ABTestManager:
    """A/Bテスト管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.active_tests = {}
        self.test_results = {}
        self.test_history = []
    
    def calculate_sample_size(self,
                            baseline_rate: float,
                            minimum_detectable_effect: float,
                            alpha: float = 0.05,
                            power: float = 0.8,
                            two_tailed: bool = True) -> int:
        """
        必要サンプルサイズの計算
        
        Args:
            baseline_rate: ベースライン転換率
            minimum_detectable_effect: 最小検出効果
            alpha: 有意水準
            power: 検出力
            two_tailed: 両側検定か
        
        Returns:
            必要サンプルサイズ
        """
        # Z値の計算
        if two_tailed:
            z_alpha = stats.norm.ppf(1 - alpha/2)
        else:
            z_alpha = stats.norm.ppf(1 - alpha)
        
        z_beta = stats.norm.ppf(power)
        
        # プールされた分散
        p1 = baseline_rate
        p2 = baseline_rate + minimum_detectable_effect
        p_pooled = (p1 + p2) / 2
        
        # サンプルサイズ計算
        numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
        denominator = (p2 - p1) ** 2
        
        sample_size = int(np.ceil(numerator / denominator))
        
        logger.info(f"Calculated sample size: {sample_size} per variant")
        
        return sample_size
    
    def create_test(self, config: ABTestConfig) -> str:
        """
        新規テスト作成
        
        Args:
            config: テスト設定
        
        Returns:
            テストID
        """
        test_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        test_data = {
            'id': test_id,
            'config': config,
            'status': TestStatus.PLANNING,
            'created_at': datetime.now().isoformat(),
            'start_date': None,
            'end_date': None,
            'data': {
                'variant_a': [],
                'variant_b': []
            },
            'results': None
        }
        
        self.active_tests[test_id] = test_data
        
        logger.info(f"Created new A/B test: {test_id}")
        
        return test_id
    
    def start_test(self, test_id: str) -> bool:
        """
        テスト開始
        
        Args:
            test_id: テストID
        
        Returns:
            成功フラグ
        """
        if test_id not in self.active_tests:
            logger.error(f"Test {test_id} not found")
            return False
        
        test = self.active_tests[test_id]
        test['status'] = TestStatus.RUNNING
        test['start_date'] = datetime.now().isoformat()
        
        # 終了予定日の設定
        config = test['config']
        end_date = datetime.now() + timedelta(days=config.test_duration_days)
        test['end_date'] = end_date.isoformat()
        
        logger.info(f"Started test {test_id}")
        
        return True
    
    def record_conversion(self, test_id: str, variant: str, user_id: str,
                         converted: bool, metadata: Optional[Dict] = None):
        """
        コンバージョン記録
        
        Args:
            test_id: テストID
            variant: バリアント（'a' or 'b'）
            user_id: ユーザーID
            converted: コンバージョンフラグ
            metadata: 追加メタデータ
        """
        if test_id not in self.active_tests:
            logger.error(f"Test {test_id} not found")
            return
        
        test = self.active_tests[test_id]
        
        if test['status'] != TestStatus.RUNNING:
            logger.warning(f"Test {test_id} is not running")
            return
        
        # データ記録
        data_point = {
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'converted': converted,
            'metadata': metadata or {}
        }
        
        if variant == 'a':
            test['data']['variant_a'].append(data_point)
        elif variant == 'b':
            test['data']['variant_b'].append(data_point)
        else:
            logger.error(f"Invalid variant: {variant}")
    
    def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """
        テスト結果分析
        
        Args:
            test_id: テストID
        
        Returns:
            分析結果
        """
        if test_id not in self.active_tests:
            logger.error(f"Test {test_id} not found")
            return {}
        
        test = self.active_tests[test_id]
        data_a = test['data']['variant_a']
        data_b = test['data']['variant_b']
        
        if not data_a or not data_b:
            logger.warning("Insufficient data for analysis")
            return {'error': 'Insufficient data'}
        
        # コンバージョン率計算
        conversions_a = sum(1 for d in data_a if d['converted'])
        conversions_b = sum(1 for d in data_b if d['converted'])
        
        n_a = len(data_a)
        n_b = len(data_b)
        
        rate_a = conversions_a / n_a if n_a > 0 else 0
        rate_b = conversions_b / n_b if n_b > 0 else 0
        
        # 統計的有意性検定
        significance = self._test_statistical_significance(
            conversions_a, n_a, conversions_b, n_b
        )
        
        # リフト計算
        lift = ((rate_b - rate_a) / rate_a * 100) if rate_a > 0 else 0
        
        # 信頼区間計算
        ci_a = self._calculate_confidence_interval(conversions_a, n_a)
        ci_b = self._calculate_confidence_interval(conversions_b, n_b)
        
        results = {
            'variant_a': {
                'sample_size': n_a,
                'conversions': conversions_a,
                'conversion_rate': rate_a,
                'confidence_interval': ci_a
            },
            'variant_b': {
                'sample_size': n_b,
                'conversions': conversions_b,
                'conversion_rate': rate_b,
                'confidence_interval': ci_b
            },
            'lift': lift,
            'p_value': significance['p_value'],
            'is_significant': significance['is_significant'],
            'statistical_power': self._calculate_observed_power(
                conversions_a, n_a, conversions_b, n_b
            ),
            'recommendation': self._generate_recommendation(
                rate_a, rate_b, significance['is_significant'], n_a, n_b
            )
        }
        
        # 結果保存
        test['results'] = results
        
        return results
    
    def _test_statistical_significance(self,
                                     successes_a: int, n_a: int,
                                     successes_b: int, n_b: int,
                                     alpha: float = 0.05) -> Dict[str, Any]:
        """
        統計的有意性検定（カイ二乗検定）
        
        Args:
            successes_a: A群の成功数
            n_a: A群のサンプルサイズ
            successes_b: B群の成功数
            n_b: B群のサンプルサイズ
            alpha: 有意水準
        
        Returns:
            検定結果
        """
        # 分割表作成
        contingency_table = np.array([
            [successes_a, n_a - successes_a],
            [successes_b, n_b - successes_b]
        ])
        
        # カイ二乗検定
        chi2, p_value, dof, expected = chi2_contingency(contingency_table)
        
        is_significant = p_value < alpha
        
        return {
            'chi2': chi2,
            'p_value': p_value,
            'is_significant': is_significant,
            'alpha': alpha
        }
    
    def _calculate_confidence_interval(self, successes: int, n: int,
                                      confidence_level: float = 0.95) -> Tuple[float, float]:
        """
        二項比率の信頼区間計算（Wilson Score Interval）
        
        Args:
            successes: 成功数
            n: サンプルサイズ
            confidence_level: 信頼水準
        
        Returns:
            信頼区間（下限、上限）
        """
        if n == 0:
            return (0, 0)
        
        p_hat = successes / n
        z = stats.norm.ppf((1 + confidence_level) / 2)
        
        denominator = 1 + z**2 / n
        centre = (p_hat + z**2 / (2 * n)) / denominator
        offset = z * np.sqrt(p_hat * (1 - p_hat) / n + z**2 / (4 * n**2)) / denominator
        
        lower = max(0, centre - offset)
        upper = min(1, centre + offset)
        
        return (lower, upper)
    
    def _calculate_observed_power(self,
                                 successes_a: int, n_a: int,
                                 successes_b: int, n_b: int) -> float:
        """
        観測された検出力の計算
        
        Args:
            successes_a: A群の成功数
            n_a: A群のサンプルサイズ
            successes_b: B群の成功数
            n_b: B群のサンプルサイズ
        
        Returns:
            検出力
        """
        if n_a == 0 or n_b == 0:
            return 0.0
        
        p_a = successes_a / n_a
        p_b = successes_b / n_b
        
        # プールされた比率
        p_pooled = (successes_a + successes_b) / (n_a + n_b)
        
        # 効果サイズ
        effect_size = abs(p_b - p_a) / np.sqrt(p_pooled * (1 - p_pooled))
        
        # 近似的な検出力計算
        n_harmonic = 2 * n_a * n_b / (n_a + n_b)
        power = 1 - stats.norm.cdf(1.96 - effect_size * np.sqrt(n_harmonic / 2))
        
        return min(1.0, max(0.0, power))
    
    def _generate_recommendation(self,
                                rate_a: float, rate_b: float,
                                is_significant: bool,
                                n_a: int, n_b: int) -> str:
        """
        推奨事項生成
        
        Args:
            rate_a: A群のコンバージョン率
            rate_b: B群のコンバージョン率
            is_significant: 統計的有意性
            n_a: A群のサンプルサイズ
            n_b: B群のサンプルサイズ
        
        Returns:
            推奨事項
        """
        min_sample = 100  # 最小サンプルサイズ
        
        if n_a < min_sample or n_b < min_sample:
            return "サンプルサイズが不足しています。テストを継続してください。"
        
        if is_significant:
            if rate_b > rate_a:
                improvement = ((rate_b - rate_a) / rate_a * 100)
                return f"バリアントBが統計的に有意に優れています（+{improvement:.1f}%）。Bの採用を推奨します。"
            else:
                decline = ((rate_a - rate_b) / rate_a * 100)
                return f"バリアントAが統計的に有意に優れています（-{decline:.1f}%）。Aの継続を推奨します。"
        else:
            if abs(rate_b - rate_a) < 0.01:
                return "両バリアントに有意な差はありません。コスト等を考慮して選択してください。"
            else:
                return "統計的有意性は検出されませんでした。テストの継続または再設計を検討してください。"
    
    def simulate_test(self,
                     true_rate_a: float,
                     true_rate_b: float,
                     sample_size: int,
                     num_simulations: int = 1000) -> Dict[str, Any]:
        """
        A/Bテストのシミュレーション
        
        Args:
            true_rate_a: A群の真の転換率
            true_rate_b: B群の真の転換率
            sample_size: サンプルサイズ
            num_simulations: シミュレーション回数
        
        Returns:
            シミュレーション結果
        """
        significant_results = 0
        correct_decisions = 0
        type_i_errors = 0
        type_ii_errors = 0
        
        for _ in range(num_simulations):
            # データ生成
            conversions_a = np.random.binomial(sample_size, true_rate_a)
            conversions_b = np.random.binomial(sample_size, true_rate_b)
            
            # 有意性検定
            sig_test = self._test_statistical_significance(
                conversions_a, sample_size,
                conversions_b, sample_size
            )
            
            if sig_test['is_significant']:
                significant_results += 1
                
                # 正しい判定かチェック
                observed_better = (conversions_b / sample_size) > (conversions_a / sample_size)
                true_better = true_rate_b > true_rate_a
                
                if observed_better == true_better:
                    correct_decisions += 1
            
            # エラータイプ分類
            if true_rate_a == true_rate_b and sig_test['is_significant']:
                type_i_errors += 1
            elif true_rate_a != true_rate_b and not sig_test['is_significant']:
                type_ii_errors += 1
        
        return {
            'power': significant_results / num_simulations,
            'accuracy': correct_decisions / num_simulations if significant_results > 0 else 0,
            'type_i_error_rate': type_i_errors / num_simulations,
            'type_ii_error_rate': type_ii_errors / num_simulations,
            'num_simulations': num_simulations
        }
    
    def calculate_test_duration(self,
                              daily_traffic: int,
                              required_sample_size: int,
                              allocation_ratio: float = 0.5) -> int:
        """
        必要テスト期間の計算
        
        Args:
            daily_traffic: 日次トラフィック
            required_sample_size: 必要サンプルサイズ
            allocation_ratio: テストへの割り当て比率
        
        Returns:
            必要日数
        """
        effective_daily_traffic = daily_traffic * allocation_ratio
        days_needed = int(np.ceil(required_sample_size * 2 / effective_daily_traffic))
        
        # 最小期間（1週間）と最大期間（4週間）の制約
        days_needed = max(7, min(28, days_needed))
        
        return days_needed
    
    def get_test_summary(self, test_id: str) -> Dict[str, Any]:
        """
        テストサマリー取得
        
        Args:
            test_id: テストID
        
        Returns:
            サマリー情報
        """
        if test_id not in self.active_tests:
            return {'error': 'Test not found'}
        
        test = self.active_tests[test_id]
        config = test['config']
        
        summary = {
            'test_id': test_id,
            'test_name': config.test_name,
            'status': test['status'].value if isinstance(test['status'], TestStatus) else test['status'],
            'created_at': test['created_at'],
            'start_date': test['start_date'],
            'end_date': test['end_date'],
            'variant_a_description': config.variant_a,
            'variant_b_description': config.variant_b,
            'current_sample_sizes': {
                'variant_a': len(test['data']['variant_a']),
                'variant_b': len(test['data']['variant_b'])
            },
            'target_sample_size': config.sample_size,
            'primary_metric': config.primary_metric
        }
        
        # 結果がある場合は追加
        if test['results']:
            summary['results'] = test['results']
        
        return summary
    
    def export_test_results(self, test_id: str, format: str = 'json') -> str:
        """
        テスト結果エクスポート
        
        Args:
            test_id: テストID
            format: 出力形式（'json', 'csv'）
        
        Returns:
            エクスポートデータ
        """
        if test_id not in self.active_tests:
            return None
        
        test = self.active_tests[test_id]
        
        if format == 'json':
            return json.dumps(test, default=str, indent=2)
        
        elif format == 'csv':
            # CSVフォーマットでエクスポート
            data_rows = []
            
            for variant in ['variant_a', 'variant_b']:
                for record in test['data'][variant]:
                    data_rows.append({
                        'test_id': test_id,
                        'variant': variant,
                        'user_id': record['user_id'],
                        'timestamp': record['timestamp'],
                        'converted': record['converted']
                    })
            
            df = pd.DataFrame(data_rows)
            return df.to_csv(index=False)
        
        return None