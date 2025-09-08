"""
モデル説明モジュール
SHAPを使用してモデルの予測根拠を可視化
"""

import shap
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from typing import Optional, Dict, List, Any, Union
import logging
import json
import base64
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ModelExplainer:
    """モデルの予測を説明するクラス"""
    
    def __init__(self, model, feature_names: List[str], background_data: Optional[pd.DataFrame] = None):
        """
        初期化
        
        Args:
            model: 学習済みモデル
            feature_names: 特徴量名のリスト
            background_data: SHAP値計算用の背景データ
        """
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        self.background_data = background_data
        
        # SHAP Explainerを初期化
        self._initialize_explainer()
        
    def _initialize_explainer(self):
        """SHAP Explainerを初期化"""
        try:
            if self.background_data is not None:
                # TreeExplainerを使用（ランダムフォレスト用）
                self.explainer = shap.TreeExplainer(
                    self.model, 
                    self.background_data,
                    feature_names=self.feature_names
                )
            else:
                # 背景データなしで初期化
                self.explainer = shap.TreeExplainer(self.model)
            
            logger.info("SHAP explainer initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize SHAP explainer: {e}")
            # フォールバック: Explainerを使用
            self.explainer = shap.Explainer(self.model)
    
    def explain_prediction(self, X: pd.DataFrame) -> np.ndarray:
        """
        個別予測のSHAP値を計算
        
        Args:
            X: 説明対象のデータ
            
        Returns:
            SHAP値の配列
        """
        if self.explainer is None:
            raise ValueError("Explainer not initialized")
        
        shap_values = self.explainer.shap_values(X)
        
        # 二値分類の場合、正クラスのSHAP値を返す
        if isinstance(shap_values, list) and len(shap_values) == 2:
            return shap_values[1]
        
        return shap_values
    
    def create_waterfall_plot(self, 
                            X_single: pd.DataFrame,
                            max_display: int = 10) -> Dict[str, Any]:
        """
        ウォーターフォールプロット用のデータを生成
        
        Args:
            X_single: 単一サンプルのデータ
            max_display: 表示する特徴量の最大数
            
        Returns:
            プロット用のデータ辞書
        """
        # SHAP値を計算
        shap_values = self.explain_prediction(X_single)
        
        if len(shap_values.shape) > 1:
            shap_values = shap_values[0]
        
        # 特徴量とSHAP値をペアにしてソート
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'shap_value': shap_values,
            'feature_value': X_single.iloc[0].values
        })
        
        # 絶対値でソートして上位を選択
        feature_importance['abs_shap'] = abs(feature_importance['shap_value'])
        feature_importance = feature_importance.nlargest(max_display, 'abs_shap')
        feature_importance = feature_importance.sort_values('shap_value')
        
        # 基準値と予測値
        if hasattr(self.explainer, 'expected_value'):
            if isinstance(self.explainer.expected_value, np.ndarray):
                base_value = self.explainer.expected_value[1] if len(self.explainer.expected_value) > 1 else self.explainer.expected_value[0]
            else:
                base_value = self.explainer.expected_value
        else:
            base_value = 0.5
        
        prediction_value = base_value + shap_values.sum()
        
        return {
            'features': feature_importance['feature'].tolist(),
            'shap_values': feature_importance['shap_value'].tolist(),
            'feature_values': feature_importance['feature_value'].tolist(),
            'base_value': float(base_value),
            'prediction_value': float(prediction_value)
        }
    
    def create_force_plot_data(self, X_single: pd.DataFrame) -> Dict[str, Any]:
        """
        フォースプロット用のデータを生成
        
        Args:
            X_single: 単一サンプルのデータ
            
        Returns:
            プロット用のデータ辞書
        """
        # SHAP値を計算
        shap_values = self.explain_prediction(X_single)
        
        if len(shap_values.shape) > 1:
            shap_values = shap_values[0]
        
        # 基準値
        if hasattr(self.explainer, 'expected_value'):
            if isinstance(self.explainer.expected_value, np.ndarray):
                base_value = self.explainer.expected_value[1] if len(self.explainer.expected_value) > 1 else self.explainer.expected_value[0]
            else:
                base_value = self.explainer.expected_value
        else:
            base_value = 0.5
        
        # 正と負の寄与を分離
        positive_features = []
        negative_features = []
        
        for i, (feature, value) in enumerate(zip(self.feature_names, shap_values)):
            feature_data = {
                'feature': feature,
                'value': float(value),
                'feature_value': float(X_single.iloc[0, i])
            }
            
            if value > 0:
                positive_features.append(feature_data)
            else:
                negative_features.append(feature_data)
        
        # ソート
        positive_features.sort(key=lambda x: abs(x['value']), reverse=True)
        negative_features.sort(key=lambda x: abs(x['value']), reverse=True)
        
        return {
            'base_value': float(base_value),
            'prediction': float(base_value + shap_values.sum()),
            'positive_features': positive_features[:5],  # Top 5
            'negative_features': negative_features[:5]   # Top 5
        }
    
    def create_summary_plot_data(self, X: pd.DataFrame, max_features: int = 20) -> Dict[str, Any]:
        """
        サマリープロット用のデータを生成
        
        Args:
            X: 複数サンプルのデータ
            max_features: 表示する特徴量の最大数
            
        Returns:
            プロット用のデータ辞書
        """
        # SHAP値を計算
        shap_values = self.explain_prediction(X)
        
        # 特徴量の重要度（絶対値の平均）
        feature_importance = pd.DataFrame({
            'feature': self.feature_names,
            'importance': np.abs(shap_values).mean(axis=0)
        }).nlargest(max_features, 'importance')
        
        # 選択された特徴量のインデックス
        selected_indices = [self.feature_names.index(f) for f in feature_importance['feature']]
        
        # 各特徴量のSHAP値と実際の値
        plot_data = []
        for idx in selected_indices:
            feature_name = self.feature_names[idx]
            for i in range(len(X)):
                plot_data.append({
                    'feature': feature_name,
                    'shap_value': float(shap_values[i, idx]),
                    'feature_value': float(X.iloc[i, idx]),
                    'importance': float(feature_importance[feature_importance['feature'] == feature_name]['importance'].iloc[0])
                })
        
        return {
            'data': plot_data,
            'features': feature_importance['feature'].tolist(),
            'importances': feature_importance['importance'].tolist()
        }
    
    def create_dependence_plot_data(self, 
                                  X: pd.DataFrame,
                                  feature_name: str,
                                  interaction_feature: Optional[str] = None) -> Dict[str, Any]:
        """
        依存プロット用のデータを生成
        
        Args:
            X: データ
            feature_name: 対象特徴量名
            interaction_feature: 相互作用を見る特徴量名
            
        Returns:
            プロット用のデータ辞書
        """
        if feature_name not in self.feature_names:
            raise ValueError(f"Feature '{feature_name}' not found")
        
        # SHAP値を計算
        shap_values = self.explain_prediction(X)
        
        # 特徴量のインデックス
        feature_idx = self.feature_names.index(feature_name)
        
        # データ準備
        plot_data = {
            'feature_values': X.iloc[:, feature_idx].tolist(),
            'shap_values': shap_values[:, feature_idx].tolist()
        }
        
        # 相互作用特徴量がある場合
        if interaction_feature and interaction_feature in self.feature_names:
            interaction_idx = self.feature_names.index(interaction_feature)
            plot_data['interaction_values'] = X.iloc[:, interaction_idx].tolist()
            plot_data['interaction_feature'] = interaction_feature
        
        return plot_data
    
    def get_feature_importance_ranking(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        特徴量の重要度ランキングを取得
        
        Args:
            X: データ
            
        Returns:
            重要度ランキングのDataFrame
        """
        # SHAP値を計算
        shap_values = self.explain_prediction(X)
        
        # 各特徴量の重要度を計算
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance_mean': np.abs(shap_values).mean(axis=0),
            'importance_std': np.abs(shap_values).std(axis=0),
            'positive_impact': (shap_values > 0).mean(axis=0),
            'negative_impact': (shap_values < 0).mean(axis=0)
        })
        
        # ソート
        importance_df = importance_df.sort_values('importance_mean', ascending=False)
        importance_df['rank'] = range(1, len(importance_df) + 1)
        
        return importance_df
    
    def generate_explanation_report(self, 
                                   X_single: pd.DataFrame,
                                   product_name: str = "Product") -> Dict[str, Any]:
        """
        予測の詳細な説明レポートを生成
        
        Args:
            X_single: 単一サンプルのデータ
            product_name: 製品名
            
        Returns:
            説明レポートの辞書
        """
        # 予測値を取得
        prediction_proba = self.model.predict_proba(X_single)[0, 1]
        
        # SHAP値を計算
        shap_values = self.explain_prediction(X_single)
        if len(shap_values.shape) > 1:
            shap_values = shap_values[0]
        
        # トップ要因を抽出
        feature_impact = pd.DataFrame({
            'feature': self.feature_names,
            'shap_value': shap_values,
            'abs_shap': abs(shap_values)
        }).nlargest(10, 'abs_shap')
        
        # ポジティブ/ネガティブ要因を分離
        positive_factors = feature_impact[feature_impact['shap_value'] > 0].to_dict('records')
        negative_factors = feature_impact[feature_impact['shap_value'] < 0].to_dict('records')
        
        # リスクレベルを判定
        if prediction_proba >= 0.7:
            risk_level = "Low Risk / High Potential"
            risk_color = "success"
        elif prediction_proba >= 0.4:
            risk_level = "Medium Risk / Medium Potential"
            risk_color = "warning"
        else:
            risk_level = "High Risk / Low Potential"
            risk_color = "danger"
        
        # レポート生成
        report = {
            'product_name': product_name,
            'prediction': {
                'probability': float(prediction_proba),
                'percentage': f"{prediction_proba * 100:.1f}%",
                'risk_level': risk_level,
                'risk_color': risk_color
            },
            'key_factors': {
                'positive': positive_factors,
                'negative': negative_factors,
                'top_positive': positive_factors[0] if positive_factors else None,
                'top_negative': negative_factors[0] if negative_factors else None
            },
            'recommendations': self._generate_recommendations(feature_impact, prediction_proba)
        }
        
        return report
    
    def _generate_recommendations(self, 
                                feature_impact: pd.DataFrame,
                                prediction_proba: float) -> List[str]:
        """
        改善推奨事項を生成
        
        Args:
            feature_impact: 特徴量の影響度
            prediction_proba: 予測確率
            
        Returns:
            推奨事項のリスト
        """
        recommendations = []
        
        # ネガティブ要因に基づく推奨
        negative_factors = feature_impact[feature_impact['shap_value'] < 0]
        
        for _, row in negative_factors.iterrows():
            feature = row['feature']
            
            if 'buzz' in feature.lower() or 'news' in feature.lower():
                recommendations.append("📰 メディア露出を増やすためのPR戦略を強化")
            elif 'academic' in feature.lower() or 'paper' in feature.lower():
                recommendations.append("🔬 科学的根拠の強化と研究成果の活用")
            elif 'competitor' in feature.lower():
                recommendations.append("🎯 競合差別化戦略の明確化")
            elif 'price' in feature.lower():
                recommendations.append("💰 価格戦略の見直しと価値提案の強化")
            elif 'novelty' in feature.lower() or 'innovation' in feature.lower():
                recommendations.append("💡 製品の独自性・新規性のアピール強化")
        
        # 予測確率に基づく一般的な推奨
        if prediction_proba < 0.5:
            recommendations.append("⚠️ 全体的な製品戦略の見直しを推奨")
        elif prediction_proba < 0.7:
            recommendations.append("📈 マーケティング施策の強化で成功確率向上の余地あり")
        else:
            recommendations.append("✅ 現在の戦略を維持しつつ、細部の最適化を継続")
        
        # 重複を削除して最大5つまで
        return list(dict.fromkeys(recommendations))[:5]


class InteractivePlotter:
    """インタラクティブなプロット生成クラス"""
    
    @staticmethod
    def create_waterfall_plot(waterfall_data: Dict[str, Any]) -> go.Figure:
        """
        Plotlyでウォーターフォールプロットを作成
        
        Args:
            waterfall_data: ウォーターフォールプロット用データ
            
        Returns:
            Plotlyフィギュア
        """
        features = waterfall_data['features']
        values = waterfall_data['shap_values']
        
        # 累積値を計算
        cumulative = [waterfall_data['base_value']]
        for v in values:
            cumulative.append(cumulative[-1] + v)
        
        # カラー設定
        colors = ['lightgray'] + ['red' if v < 0 else 'green' for v in values] + ['blue']
        
        # プロット作成
        fig = go.Figure(go.Waterfall(
            name="SHAP",
            orientation="v",
            measure=["relative"] * len(values) + ["total"],
            x=['Base'] + features + ['Prediction'],
            y=[waterfall_data['base_value']] + values + [waterfall_data['prediction_value']],
            connector={"line": {"color": "rgb(63, 63, 63)"}},
            decreasing={"marker": {"color": "rgba(219, 64, 82, 0.7)"}},
            increasing={"marker": {"color": "rgba(50, 171, 96, 0.7)"}},
            totals={"marker": {"color": "rgba(55, 128, 191, 0.7)"}}
        ))
        
        fig.update_layout(
            title="予測への各特徴量の寄与度",
            xaxis_title="特徴量",
            yaxis_title="予測確率",
            showlegend=False,
            height=500
        )
        
        return fig
    
    @staticmethod
    def create_force_plot(force_data: Dict[str, Any]) -> go.Figure:
        """
        Plotlyでフォースプロットを作成
        
        Args:
            force_data: フォースプロット用データ
            
        Returns:
            Plotlyフィギュア
        """
        # データ準備
        positive_values = [f['value'] for f in force_data['positive_features']]
        positive_labels = [f"{f['feature']}: {f['value']:.3f}" for f in force_data['positive_features']]
        
        negative_values = [f['value'] for f in force_data['negative_features']]
        negative_labels = [f"{f['feature']}: {f['value']:.3f}" for f in force_data['negative_features']]
        
        # プロット作成
        fig = go.Figure()
        
        # ポジティブ要因
        if positive_values:
            fig.add_trace(go.Bar(
                y=positive_labels,
                x=positive_values,
                orientation='h',
                name='Positive',
                marker_color='rgba(50, 171, 96, 0.7)'
            ))
        
        # ネガティブ要因
        if negative_values:
            fig.add_trace(go.Bar(
                y=negative_labels,
                x=negative_values,
                orientation='h',
                name='Negative',
                marker_color='rgba(219, 64, 82, 0.7)'
            ))
        
        fig.update_layout(
            title=f"予測値: {force_data['prediction']:.3f} (基準値: {force_data['base_value']:.3f})",
            xaxis_title="SHAP値",
            yaxis_title="特徴量",
            barmode='overlay',
            height=400
        )
        
        return fig
    
    @staticmethod
    def create_summary_plot(summary_data: Dict[str, Any]) -> go.Figure:
        """
        Plotlyでサマリープロットを作成
        
        Args:
            summary_data: サマリープロット用データ
            
        Returns:
            Plotlyフィギュア
        """
        df = pd.DataFrame(summary_data['data'])
        
        # プロット作成
        fig = px.scatter(
            df, 
            x='shap_value', 
            y='feature',
            color='feature_value',
            color_continuous_scale='RdBu',
            labels={'shap_value': 'SHAP値', 'feature': '特徴量', 'feature_value': '特徴量の値'},
            title='特徴量の重要度と影響'
        )
        
        fig.update_layout(
            height=600,
            yaxis={'categoryorder': 'total ascending'}
        )
        
        return fig


def main():
    """テスト実行関数"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from src.models.basic_model import HitPredictionModel, generate_dummy_data
    
    logger.info("=== Model Explainer Test ===")
    
    # ダミーデータ生成
    data, labels = generate_dummy_data(100)
    
    # モデル学習
    model = HitPredictionModel()
    X = model.prepare_features(data)
    model.train(X, labels, validate=False)
    
    # Explainer初期化
    explainer = ModelExplainer(
        model.model,
        feature_names=X.columns.tolist(),
        background_data=X[:50]  # 背景データとして半分を使用
    )
    
    # 単一予測の説明
    X_test = X.iloc[[0]]
    
    logger.info("\n1. Generating waterfall plot data...")
    waterfall_data = explainer.create_waterfall_plot(X_test)
    logger.info(f"   Base value: {waterfall_data['base_value']:.3f}")
    logger.info(f"   Prediction: {waterfall_data['prediction_value']:.3f}")
    
    logger.info("\n2. Generating force plot data...")
    force_data = explainer.create_force_plot_data(X_test)
    logger.info(f"   Top positive factor: {force_data['positive_features'][0] if force_data['positive_features'] else 'None'}")
    logger.info(f"   Top negative factor: {force_data['negative_features'][0] if force_data['negative_features'] else 'None'}")
    
    logger.info("\n3. Generating summary plot data...")
    summary_data = explainer.create_summary_plot_data(X[:20])
    logger.info(f"   Analyzed {len(summary_data['features'])} features")
    
    logger.info("\n4. Generating explanation report...")
    report = explainer.generate_explanation_report(X_test, "Test Product")
    logger.info(f"   Prediction: {report['prediction']['percentage']}")
    logger.info(f"   Risk Level: {report['prediction']['risk_level']}")
    logger.info(f"   Recommendations: {len(report['recommendations'])} items")
    
    logger.info("\n✅ Model explainer test completed!")
    
    return explainer


if __name__ == "__main__":
    main()