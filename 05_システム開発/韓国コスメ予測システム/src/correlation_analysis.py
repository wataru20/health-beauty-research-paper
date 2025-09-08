import pandas as pd
import numpy as np
from scipy import stats
from scipy.signal import correlate
from typing import Dict, Tuple, List
import warnings
warnings.filterwarnings('ignore')


class KoreaJapanCorrelationAnalyzer:
    """日韓市場相関分析システム"""
    
    def __init__(self):
        self.weights = {
            'rank_correlation': 0.3,
            'time_series': 0.5,
            'category': 0.2
        }
        
    def spearman_rank_analysis(self, 
                               korea_ranks: pd.Series, 
                               japan_ranks: pd.Series) -> Dict:
        """第1段階：スピアマン順位相関分析"""
        
        correlation, p_value = stats.spearmanr(korea_ranks, japan_ranks)
        
        return {
            'correlation': correlation,
            'p_value': p_value,
            'significant': p_value < 0.05 and abs(correlation) > 0.6,
            'strength': self._interpret_correlation(correlation)
        }
    
    def cross_correlation_analysis(self,
                                  korea_data: pd.Series,
                                  japan_data: pd.Series,
                                  max_lag: int = 6) -> Dict:
        """第2段階：クロス相関分析（タイムラグ検出）"""
        
        # データの正規化
        korea_norm = (korea_data - korea_data.mean()) / korea_data.std()
        japan_norm = (japan_data - japan_data.mean()) / japan_data.std()
        
        correlations = {}
        for lag in range(max_lag + 1):
            if lag == 0:
                corr, _ = stats.pearsonr(korea_norm, japan_norm)
            else:
                if len(korea_norm) > lag:
                    corr, _ = stats.pearsonr(korea_norm[:-lag], japan_norm[lag:])
                else:
                    corr = 0
            correlations[lag] = corr
        
        # 最適ラグの特定
        optimal_lag = max(correlations, key=lambda x: abs(correlations[x]))
        
        return {
            'correlations_by_lag': correlations,
            'optimal_lag': optimal_lag,
            'optimal_correlation': correlations[optimal_lag],
            'lag_interpretation': f"韓国トレンドが{optimal_lag}ヶ月後に日本市場に波及"
        }
    
    def category_correlation(self,
                            category_korea: str,
                            category_japan: str,
                            category_matrix: pd.DataFrame = None) -> float:
        """第3段階：カテゴリ相関度算出"""
        
        # カテゴリマトリックスが提供されない場合のデフォルト値
        if category_matrix is None:
            default_correlations = {
                ('スキンケア', 'スキンケア'): 0.9,
                ('メイクアップ', 'メイクアップ'): 0.85,
                ('クレンジング', 'クレンジング'): 0.8,
                ('マスク・パック', 'マスク・パック'): 0.95,
                ('ベースメイク', 'ベースメイク'): 0.88
            }
            return default_correlations.get((category_korea, category_japan), 0.5)
        
        return category_matrix.loc[category_korea, category_japan]
    
    def calculate_prediction_score(self,
                                  rank_correlation: float,
                                  time_correlation: float,
                                  category_score: float) -> Dict:
        """統合予測スコア算出"""
        
        score = (self.weights['rank_correlation'] * rank_correlation +
                self.weights['time_series'] * time_correlation +
                self.weights['category'] * category_score)
        
        return {
            'prediction_score': score,
            'confidence_level': self._get_confidence_level(score),
            'recommendation': self._get_recommendation(score),
            'components': {
                'rank_contribution': self.weights['rank_correlation'] * rank_correlation,
                'time_contribution': self.weights['time_series'] * time_correlation,
                'category_contribution': self.weights['category'] * category_score
            }
        }
    
    def run_full_analysis(self,
                         korea_data: pd.DataFrame,
                         japan_data: pd.DataFrame) -> Dict:
        """完全な3段階分析の実行"""
        
        results = {}
        
        # 第1段階：順位相関
        if 'rank' in korea_data.columns and 'rank' in japan_data.columns:
            results['rank_analysis'] = self.spearman_rank_analysis(
                korea_data['rank'], 
                japan_data['rank']
            )
        
        # 第2段階：時系列相関
        if 'sales' in korea_data.columns and 'sales' in japan_data.columns:
            results['time_series_analysis'] = self.cross_correlation_analysis(
                korea_data['sales'],
                japan_data['sales']
            )
        
        # 第3段階：統合スコア
        if 'category' in korea_data.columns:
            category_score = self.category_correlation(
                korea_data['category'].iloc[0],
                japan_data['category'].iloc[0] if 'category' in japan_data.columns else korea_data['category'].iloc[0]
            )
            
            results['prediction'] = self.calculate_prediction_score(
                results.get('rank_analysis', {}).get('correlation', 0),
                results.get('time_series_analysis', {}).get('optimal_correlation', 0),
                category_score
            )
        
        return results
    
    def _interpret_correlation(self, corr: float) -> str:
        """相関係数の解釈"""
        abs_corr = abs(corr)
        if abs_corr >= 0.9:
            return "非常に強い相関"
        elif abs_corr >= 0.7:
            return "強い相関"
        elif abs_corr >= 0.5:
            return "中程度の相関"
        elif abs_corr >= 0.3:
            return "弱い相関"
        else:
            return "ほぼ無相関"
    
    def _get_confidence_level(self, score: float) -> str:
        """予測信頼度の判定"""
        if score >= 0.8:
            return "非常に高い"
        elif score >= 0.6:
            return "高い"
        elif score >= 0.4:
            return "中程度"
        elif score >= 0.2:
            return "低い"
        else:
            return "非常に低い"
    
    def _get_recommendation(self, score: float) -> str:
        """スコアに基づく推奨アクション"""
        if score >= 0.7:
            return "即座に日本市場投入を推奨"
        elif score >= 0.5:
            return "市場テストを実施後、投入検討"
        elif score >= 0.3:
            return "追加分析と慎重な検討が必要"
        else:
            return "現時点での投入は推奨しない"


def generate_sample_analysis():
    """サンプル分析の実行"""
    
    # サンプルデータ生成
    np.random.seed(42)
    dates = pd.date_range('2024-01', periods=12, freq='M')
    
    korea_data = pd.DataFrame({
        'date': dates,
        'rank': np.random.randint(1, 21, 12),
        'sales': np.random.uniform(1000, 5000, 12),
        'category': ['スキンケア'] * 12
    })
    
    japan_data = pd.DataFrame({
        'date': dates,
        'rank': np.random.randint(1, 21, 12),
        'sales': np.random.uniform(800, 4000, 12),
        'category': ['スキンケア'] * 12
    })
    
    # 分析実行
    analyzer = KoreaJapanCorrelationAnalyzer()
    results = analyzer.run_full_analysis(korea_data, japan_data)
    
    return results


if __name__ == "__main__":
    results = generate_sample_analysis()
    print("韓国コスメヒット予測分析結果")
    print("=" * 50)
    for key, value in results.items():
        print(f"\n{key}:")
        print(value)