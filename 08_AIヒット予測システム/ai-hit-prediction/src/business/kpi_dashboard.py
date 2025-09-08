#!/usr/bin/env python
"""
KPI Dashboard and ROI Measurement System
KPIダッシュボードとROI測定システム
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# 可視化ライブラリ
try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# データベース接続
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


class KPIMetrics:
    """KPIメトリクス管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.metrics_history = []
        self.kpi_definitions = self._define_kpis()
    
    def _define_kpis(self) -> Dict:
        """KPI定義"""
        return {
            "business_kpis": {
                "revenue_impact": {
                    "name": "売上インパクト",
                    "unit": "JPY",
                    "target": 100000000,  # 1億円
                    "calculation": "sum_of_predicted_hit_product_sales"
                },
                "hit_rate": {
                    "name": "ヒット率",
                    "unit": "%",
                    "target": 70,
                    "calculation": "successful_predictions / total_predictions * 100"
                },
                "cost_saving": {
                    "name": "コスト削減",
                    "unit": "JPY",
                    "target": 50000000,  # 5千万円
                    "calculation": "avoided_failed_product_costs"
                },
                "time_to_market": {
                    "name": "市場投入時間",
                    "unit": "days",
                    "target": 90,
                    "calculation": "average_days_from_prediction_to_launch"
                }
            },
            "operational_kpis": {
                "prediction_accuracy": {
                    "name": "予測精度",
                    "unit": "%",
                    "target": 95,
                    "calculation": "correct_predictions / total_predictions * 100"
                },
                "api_response_time": {
                    "name": "APIレスポンスタイム",
                    "unit": "ms",
                    "target": 200,
                    "calculation": "p95_response_time"
                },
                "system_uptime": {
                    "name": "システム稼働率",
                    "unit": "%",
                    "target": 99.9,
                    "calculation": "uptime_minutes / total_minutes * 100"
                },
                "data_freshness": {
                    "name": "データ鮮度",
                    "unit": "hours",
                    "target": 24,
                    "calculation": "hours_since_last_update"
                }
            },
            "usage_kpis": {
                "daily_active_users": {
                    "name": "DAU",
                    "unit": "users",
                    "target": 100,
                    "calculation": "unique_daily_users"
                },
                "predictions_per_day": {
                    "name": "日次予測数",
                    "unit": "predictions",
                    "target": 50,
                    "calculation": "daily_prediction_count"
                },
                "user_satisfaction": {
                    "name": "ユーザー満足度",
                    "unit": "score",
                    "target": 4.5,
                    "calculation": "average_user_rating"
                },
                "feature_adoption": {
                    "name": "機能利用率",
                    "unit": "%",
                    "target": 80,
                    "calculation": "features_used / total_features * 100"
                }
            }
        }
    
    def calculate_kpi(self, kpi_type: str, kpi_name: str, 
                     data: Dict) -> Dict:
        """
        KPI計算
        
        Args:
            kpi_type: KPIタイプ
            kpi_name: KPI名
            data: 計算用データ
        
        Returns:
            KPI値
        """
        if kpi_type not in self.kpi_definitions:
            return {"error": "Invalid KPI type"}
        
        if kpi_name not in self.kpi_definitions[kpi_type]:
            return {"error": "Invalid KPI name"}
        
        kpi_def = self.kpi_definitions[kpi_type][kpi_name]
        
        # 実際の計算ロジック（簡略化）
        value = self._calculate_value(kpi_name, data)
        
        # ターゲット達成率
        achievement_rate = (value / kpi_def["target"] * 100) if kpi_def["target"] > 0 else 0
        
        result = {
            "name": kpi_def["name"],
            "value": value,
            "unit": kpi_def["unit"],
            "target": kpi_def["target"],
            "achievement_rate": achievement_rate,
            "status": self._get_status(achievement_rate),
            "timestamp": datetime.now().isoformat()
        }
        
        self.metrics_history.append(result)
        return result
    
    def _calculate_value(self, kpi_name: str, data: Dict) -> float:
        """実際のKPI値計算"""
        # シミュレーションデータ
        kpi_values = {
            "revenue_impact": np.random.uniform(80000000, 120000000),
            "hit_rate": np.random.uniform(65, 75),
            "cost_saving": np.random.uniform(40000000, 60000000),
            "time_to_market": np.random.uniform(80, 100),
            "prediction_accuracy": np.random.uniform(93, 97),
            "api_response_time": np.random.uniform(150, 250),
            "system_uptime": np.random.uniform(99.5, 99.99),
            "data_freshness": np.random.uniform(12, 36),
            "daily_active_users": np.random.randint(80, 120),
            "predictions_per_day": np.random.randint(40, 60),
            "user_satisfaction": np.random.uniform(4.2, 4.8),
            "feature_adoption": np.random.uniform(70, 90)
        }
        
        return kpi_values.get(kpi_name, 0)
    
    def _get_status(self, achievement_rate: float) -> str:
        """ステータス判定"""
        if achievement_rate >= 100:
            return "excellent"
        elif achievement_rate >= 80:
            return "good"
        elif achievement_rate >= 60:
            return "warning"
        else:
            return "critical"
    
    def get_kpi_summary(self) -> Dict:
        """KPIサマリー取得"""
        summary = {}
        
        for kpi_type, kpis in self.kpi_definitions.items():
            summary[kpi_type] = {}
            for kpi_name in kpis:
                data = {}  # 実際のデータを取得
                kpi_result = self.calculate_kpi(kpi_type, kpi_name, data)
                summary[kpi_type][kpi_name] = kpi_result
        
        return summary


class ROICalculator:
    """ROI計算クラス"""
    
    def __init__(self):
        """初期化"""
        self.roi_history = []
    
    def calculate_roi(self, 
                     investment: float,
                     returns: Dict,
                     period_months: int = 12) -> Dict:
        """
        ROI計算
        
        Args:
            investment: 投資額
            returns: リターン情報
            period_months: 期間（月）
        
        Returns:
            ROI情報
        """
        # 直接的なリターン
        direct_returns = {
            "increased_revenue": returns.get("increased_revenue", 0),
            "cost_savings": returns.get("cost_savings", 0),
            "avoided_losses": returns.get("avoided_losses", 0)
        }
        
        # 間接的なリターン
        indirect_returns = {
            "productivity_improvement": returns.get("productivity_improvement", 0),
            "time_savings": returns.get("time_savings", 0),
            "quality_improvement": returns.get("quality_improvement", 0)
        }
        
        # 総リターン
        total_direct = sum(direct_returns.values())
        total_indirect = sum(indirect_returns.values())
        total_returns = total_direct + total_indirect
        
        # ROI計算
        roi = ((total_returns - investment) / investment) * 100 if investment > 0 else 0
        
        # 回収期間
        monthly_return = total_returns / period_months if period_months > 0 else 0
        payback_period = investment / monthly_return if monthly_return > 0 else float('inf')
        
        # NPV計算（割引率: 年率6%）
        discount_rate = 0.06 / 12  # 月次割引率
        npv = self._calculate_npv(
            investment, monthly_return, period_months, discount_rate
        )
        
        result = {
            "investment": investment,
            "direct_returns": direct_returns,
            "indirect_returns": indirect_returns,
            "total_returns": total_returns,
            "roi_percentage": roi,
            "payback_period_months": payback_period,
            "npv": npv,
            "period_months": period_months,
            "timestamp": datetime.now().isoformat()
        }
        
        self.roi_history.append(result)
        return result
    
    def _calculate_npv(self, investment: float, monthly_return: float,
                      period_months: int, discount_rate: float) -> float:
        """NPV計算"""
        npv = -investment
        
        for month in range(1, period_months + 1):
            npv += monthly_return / ((1 + discount_rate) ** month)
        
        return npv
    
    def project_roi(self, scenarios: List[Dict]) -> List[Dict]:
        """
        ROIシナリオ分析
        
        Args:
            scenarios: シナリオリスト
        
        Returns:
            シナリオ別ROI
        """
        projections = []
        
        for scenario in scenarios:
            roi_result = self.calculate_roi(
                scenario["investment"],
                scenario["returns"],
                scenario.get("period_months", 12)
            )
            
            roi_result["scenario_name"] = scenario["name"]
            roi_result["probability"] = scenario.get("probability", 0.5)
            
            # 期待値計算
            roi_result["expected_roi"] = (
                roi_result["roi_percentage"] * roi_result["probability"]
            )
            
            projections.append(roi_result)
        
        return projections


class DashboardGenerator:
    """ダッシュボード生成クラス"""
    
    def __init__(self):
        """初期化"""
        self.kpi_metrics = KPIMetrics()
        self.roi_calculator = ROICalculator()
    
    def create_executive_dashboard(self) -> Dict:
        """
        エグゼクティブダッシュボード作成
        
        Returns:
            ダッシュボードデータ
        """
        dashboard = {
            "title": "AI Hit Prediction System - Executive Dashboard",
            "generated_at": datetime.now().isoformat(),
            "sections": {}
        }
        
        # KPIサマリー
        dashboard["sections"]["kpi_summary"] = self.kpi_metrics.get_kpi_summary()
        
        # ROI分析
        roi_scenarios = [
            {
                "name": "Conservative",
                "investment": 50000000,
                "returns": {
                    "increased_revenue": 80000000,
                    "cost_savings": 30000000,
                    "avoided_losses": 20000000
                },
                "probability": 0.7
            },
            {
                "name": "Optimistic",
                "investment": 50000000,
                "returns": {
                    "increased_revenue": 150000000,
                    "cost_savings": 50000000,
                    "avoided_losses": 40000000
                },
                "probability": 0.3
            }
        ]
        
        dashboard["sections"]["roi_analysis"] = self.roi_calculator.project_roi(
            roi_scenarios
        )
        
        # トレンド分析
        dashboard["sections"]["trends"] = self._generate_trends()
        
        # アラート
        dashboard["sections"]["alerts"] = self._generate_alerts()
        
        return dashboard
    
    def create_operational_dashboard(self) -> Dict:
        """
        オペレーショナルダッシュボード作成
        
        Returns:
            ダッシュボードデータ
        """
        dashboard = {
            "title": "AI Hit Prediction System - Operational Dashboard",
            "generated_at": datetime.now().isoformat(),
            "sections": {}
        }
        
        # システムメトリクス
        dashboard["sections"]["system_metrics"] = {
            "uptime": "99.95%",
            "api_calls_today": 1234,
            "avg_response_time": "185ms",
            "error_rate": "0.02%",
            "active_users": 87,
            "predictions_today": 456
        }
        
        # モデルパフォーマンス
        dashboard["sections"]["model_performance"] = {
            "current_accuracy": "95.3%",
            "last_retrain": "2025-09-02",
            "next_scheduled_retrain": "2025-09-09",
            "drift_detected": False,
            "confidence_distribution": {
                "high": 72,
                "medium": 23,
                "low": 5
            }
        }
        
        # データ品質
        dashboard["sections"]["data_quality"] = {
            "completeness": "98.5%",
            "freshness": "2 hours",
            "anomalies_detected": 3,
            "data_sources_status": {
                "academic_papers": "healthy",
                "news_feeds": "healthy",
                "social_media": "degraded",
                "market_data": "healthy"
            }
        }
        
        return dashboard
    
    def _generate_trends(self) -> Dict:
        """トレンドデータ生成"""
        return {
            "revenue_trend": "increasing",
            "accuracy_trend": "stable",
            "usage_trend": "increasing",
            "cost_trend": "decreasing"
        }
    
    def _generate_alerts(self) -> List[Dict]:
        """アラート生成"""
        return [
            {
                "level": "info",
                "message": "Model retraining scheduled for next week",
                "timestamp": datetime.now().isoformat()
            },
            {
                "level": "warning",
                "message": "Social media data source showing degraded performance",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat()
            }
        ]
    
    def create_visualization(self, dashboard_data: Dict) -> Optional[Dict]:
        """
        ダッシュボード可視化
        
        Args:
            dashboard_data: ダッシュボードデータ
        
        Returns:
            Plotlyグラフ
        """
        if not PLOTLY_AVAILABLE:
            return None
        
        # KPIゲージチャート
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Revenue Impact", "Prediction Accuracy",
                "System Uptime", "User Satisfaction"
            ),
            specs=[
                [{"type": "indicator"}, {"type": "indicator"}],
                [{"type": "indicator"}, {"type": "indicator"}]
            ]
        )
        
        # ゲージ追加
        kpi_data = [
            ("Revenue", 95000000, 100000000, "JPY"),
            ("Accuracy", 95.3, 95, "%"),
            ("Uptime", 99.95, 99.9, "%"),
            ("Satisfaction", 4.6, 4.5, "score")
        ]
        
        positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
        
        for (title, value, target, suffix), (row, col) in zip(kpi_data, positions):
            fig.add_trace(
                go.Indicator(
                    mode="gauge+number+delta",
                    value=value,
                    delta={'reference': target},
                    title={'text': title},
                    number={'suffix': f" {suffix}"},
                    gauge={
                        'axis': {'range': [None, target * 1.2]},
                        'bar': {'color': "darkgreen" if value >= target else "orange"},
                        'steps': [
                            {'range': [0, target * 0.8], 'color': "lightgray"},
                            {'range': [target * 0.8, target], 'color': "gray"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': target
                        }
                    }
                ),
                row=row, col=col
            )
        
        fig.update_layout(
            title="KPI Dashboard",
            height=600,
            showlegend=False
        )
        
        return fig.to_dict()


class BusinessIntelligence:
    """BI統合クラス"""
    
    def __init__(self):
        """初期化"""
        self.dashboard_generator = DashboardGenerator()
        self.reports = []
    
    def generate_weekly_report(self) -> Dict:
        """
        週次レポート生成
        
        Returns:
            レポートデータ
        """
        report = {
            "type": "weekly",
            "period": {
                "start": (datetime.now() - timedelta(days=7)).isoformat(),
                "end": datetime.now().isoformat()
            },
            "summary": {},
            "details": {}
        }
        
        # 週次サマリー
        report["summary"] = {
            "total_predictions": 342,
            "successful_predictions": 241,
            "success_rate": "70.5%",
            "revenue_impact": "¥23,500,000",
            "top_performing_category": "Skincare",
            "user_growth": "+12%"
        }
        
        # 詳細分析
        report["details"]["predictions_by_category"] = {
            "Skincare": 145,
            "Makeup": 98,
            "Hair Care": 67,
            "Body Care": 32
        }
        
        report["details"]["top_predictions"] = [
            {
                "product": "Premium Vitamin C Serum",
                "hit_probability": 0.92,
                "confidence": 0.88,
                "category": "Skincare"
            },
            {
                "product": "Natural Lip Tint Collection",
                "hit_probability": 0.87,
                "confidence": 0.85,
                "category": "Makeup"
            },
            {
                "product": "Scalp Treatment Oil",
                "hit_probability": 0.83,
                "confidence": 0.81,
                "category": "Hair Care"
            }
        ]
        
        # 改善提案
        report["recommendations"] = [
            "Focus on Skincare category - showing highest success rate",
            "Increase data collection for Body Care products",
            "Schedule model retraining for next week"
        ]
        
        self.reports.append(report)
        return report
    
    def analyze_business_impact(self, period_days: int = 30) -> Dict:
        """
        ビジネスインパクト分析
        
        Args:
            period_days: 分析期間
        
        Returns:
            インパクト分析
        """
        impact = {
            "period_days": period_days,
            "financial_impact": {},
            "operational_impact": {},
            "strategic_impact": {}
        }
        
        # 財務インパクト
        impact["financial_impact"] = {
            "revenue_generated": 95000000,
            "costs_saved": 35000000,
            "roi": 160,
            "payback_achieved": True
        }
        
        # オペレーショナルインパクト
        impact["operational_impact"] = {
            "decision_time_reduction": "65%",
            "product_failure_rate_reduction": "40%",
            "inventory_optimization": "30%",
            "marketing_efficiency_improvement": "45%"
        }
        
        # 戦略的インパクト
        impact["strategic_impact"] = {
            "market_share_growth": "2.3%",
            "competitive_advantage": "High",
            "innovation_index": "8.5/10",
            "customer_satisfaction_improvement": "12%"
        }
        
        return impact
    
    def export_dashboard_data(self, format: str = "json") -> str:
        """
        ダッシュボードデータエクスポート
        
        Args:
            format: 出力形式
        
        Returns:
            エクスポートファイルパス
        """
        executive_dashboard = self.dashboard_generator.create_executive_dashboard()
        operational_dashboard = self.dashboard_generator.create_operational_dashboard()
        
        export_data = {
            "generated_at": datetime.now().isoformat(),
            "dashboards": {
                "executive": executive_dashboard,
                "operational": operational_dashboard
            },
            "weekly_report": self.generate_weekly_report(),
            "business_impact": self.analyze_business_impact()
        }
        
        # エクスポートディレクトリ
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format == "json":
            file_path = export_dir / f"dashboard_{timestamp}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        elif format == "csv":
            # CSVエクスポート（KPIのみ）
            file_path = export_dir / f"kpi_{timestamp}.csv"
            kpi_df = self._flatten_kpi_data(export_data["dashboards"]["executive"])
            kpi_df.to_csv(file_path, index=False)
        
        logging.info(f"Dashboard exported: {file_path}")
        return str(file_path)
    
    def _flatten_kpi_data(self, dashboard_data: Dict) -> pd.DataFrame:
        """KPIデータをフラット化"""
        rows = []
        
        if "sections" in dashboard_data and "kpi_summary" in dashboard_data["sections"]:
            for kpi_type, kpis in dashboard_data["sections"]["kpi_summary"].items():
                for kpi_name, kpi_data in kpis.items():
                    row = {
                        "kpi_type": kpi_type,
                        "kpi_name": kpi_name,
                        "value": kpi_data.get("value"),
                        "target": kpi_data.get("target"),
                        "achievement_rate": kpi_data.get("achievement_rate"),
                        "status": kpi_data.get("status")
                    }
                    rows.append(row)
        
        return pd.DataFrame(rows)


# 使用例
if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # BIシステム初期化
    bi_system = BusinessIntelligence()
    
    # ダッシュボード生成
    print("\n=== Executive Dashboard ===")
    exec_dashboard = bi_system.dashboard_generator.create_executive_dashboard()
    print(json.dumps(exec_dashboard["sections"]["kpi_summary"]["business_kpis"], 
                    indent=2, default=str))
    
    print("\n=== ROI Analysis ===")
    roi_analysis = exec_dashboard["sections"]["roi_analysis"]
    for scenario in roi_analysis:
        print(f"\n{scenario['scenario_name']} Scenario:")
        print(f"  ROI: {scenario['roi_percentage']:.1f}%")
        print(f"  NPV: ¥{scenario['npv']:,.0f}")
        print(f"  Payback: {scenario['payback_period_months']:.1f} months")
    
    print("\n=== Weekly Report ===")
    weekly_report = bi_system.generate_weekly_report()
    print(f"Success Rate: {weekly_report['summary']['success_rate']}")
    print(f"Revenue Impact: {weekly_report['summary']['revenue_impact']}")
    
    print("\n=== Business Impact ===")
    impact = bi_system.analyze_business_impact()
    print(f"ROI: {impact['financial_impact']['roi']}%")
    print(f"Market Share Growth: {impact['strategic_impact']['market_share_growth']}")
    
    # ダッシュボードエクスポート
    export_path = bi_system.export_dashboard_data("json")
    print(f"\nDashboard exported to: {export_path}")