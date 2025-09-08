#!/usr/bin/env python
"""
Real-time Dashboard for AI Hit Prediction System
リアルタイムダッシュボード機能を提供
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import altair as alt
from datetime import datetime, timedelta
import json
import time
from typing import Dict, List, Optional
import os
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.data_collection.news_collector import NewsCollector
from src.data_collection.academic_collector import AcademicPaperCollector
from src.preprocessing.data_pipeline import DataPipeline
from src.preprocessing.feature_engineering import FeatureEngineer
from src.models.basic_model import HitPredictionModel
from src.analysis.model_explainer import ModelExplainer
from src.optimization.hyperparameter_optimizer import HyperparameterOptimizer, AutoML

# ページ設定
st.set_page_config(
    page_title="AI Hit Prediction Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
    }
    .prediction-box {
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .high-prob {
        background-color: #d4f4dd;
        border: 2px solid #4caf50;
    }
    .medium-prob {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
    }
    .low-prob {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
    }
    </style>
""", unsafe_allow_html=True)


class DashboardManager:
    """ダッシュボード管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.initialize_session_state()
        self.pipeline = DataPipeline()
        self.engineer = FeatureEngineer()
        self.model = HitPredictionModel()
        self.explainer = None
        self.news_collector = NewsCollector()
        self.academic_collector = AcademicPaperCollector()
    
    def initialize_session_state(self):
        """セッション状態の初期化"""
        if 'prediction_history' not in st.session_state:
            st.session_state.prediction_history = []
        if 'market_trends' not in st.session_state:
            st.session_state.market_trends = self.generate_mock_trends()
        if 'model_performance' not in st.session_state:
            st.session_state.model_performance = self.generate_mock_performance()
        if 'real_time_data' not in st.session_state:
            st.session_state.real_time_data = []
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
    
    def generate_mock_trends(self) -> pd.DataFrame:
        """モックトレンドデータ生成"""
        dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
        categories = ['スキンケア', 'メイクアップ', 'ヘアケア', 'フレグランス']
        
        data = []
        for category in categories:
            trend_values = np.cumsum(np.random.randn(30)) + np.random.randint(50, 100)
            for date, value in zip(dates, trend_values):
                data.append({
                    'date': date,
                    'category': category,
                    'trend_score': max(0, value),
                    'buzz_score': np.random.uniform(0.3, 0.9)
                })
        
        return pd.DataFrame(data)
    
    def generate_mock_performance(self) -> Dict:
        """モックパフォーマンスデータ生成"""
        return {
            'accuracy': np.random.uniform(0.85, 0.95),
            'precision': np.random.uniform(0.80, 0.92),
            'recall': np.random.uniform(0.75, 0.88),
            'f1_score': np.random.uniform(0.78, 0.90),
            'predictions_today': np.random.randint(10, 50),
            'predictions_week': np.random.randint(100, 300),
            'predictions_month': np.random.randint(500, 1000)
        }
    
    def render_header(self):
        """ヘッダーセクションのレンダリング"""
        col1, col2, col3 = st.columns([3, 2, 1])
        
        with col1:
            st.title("🚀 AI Hit Prediction Dashboard")
            st.markdown("**化粧品ヒット予測システム - リアルタイムダッシュボード**")
        
        with col2:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.info(f"最終更新: {current_time}")
        
        with col3:
            if st.button("🔄 データ更新", use_container_width=True):
                self.update_data()
    
    def render_metrics_row(self):
        """メトリクス行のレンダリング"""
        st.markdown("### 📊 システムメトリクス")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        perf = st.session_state.model_performance
        
        with col1:
            st.metric(
                "モデル精度",
                f"{perf['accuracy']:.1%}",
                f"{np.random.uniform(-0.02, 0.05):.1%}"
            )
        
        with col2:
            st.metric(
                "本日の予測数",
                perf['predictions_today'],
                f"+{np.random.randint(1, 10)}"
            )
        
        with col3:
            st.metric(
                "週間予測数",
                perf['predictions_week'],
                f"+{np.random.randint(10, 30)}"
            )
        
        with col4:
            st.metric(
                "F1スコア",
                f"{perf['f1_score']:.3f}",
                f"{np.random.uniform(-0.01, 0.03):.3f}"
            )
        
        with col5:
            active_products = len(st.session_state.prediction_history)
            st.metric(
                "監視中の製品",
                active_products,
                f"+{max(0, active_products - 5)}" if active_products > 5 else "0"
            )
    
    def render_real_time_monitor(self):
        """リアルタイム監視セクション"""
        st.markdown("### 🔴 リアルタイムモニター")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # リアルタイムトレンドグラフ
            fig = self.create_real_time_chart()
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # ホットキーワード
            st.markdown("#### 🔥 トレンドキーワード")
            keywords = self.get_trending_keywords()
            for i, (keyword, score) in enumerate(keywords[:10], 1):
                color = "🟢" if score > 0.7 else "🟡" if score > 0.4 else "🔴"
                st.markdown(f"{i}. {color} **{keyword}** ({score:.2f})")
    
    def create_real_time_chart(self) -> go.Figure:
        """リアルタイムチャート作成"""
        # 時系列データ生成（最近1時間）
        now = datetime.now()
        times = [now - timedelta(minutes=i) for i in range(60, 0, -1)]
        
        # モックデータ生成
        buzz_scores = np.cumsum(np.random.randn(60) * 0.01) + 0.5
        sentiment_scores = np.cumsum(np.random.randn(60) * 0.01) + 0.6
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('バズスコア推移', 'センチメント推移'),
            vertical_spacing=0.15
        )
        
        # バズスコア
        fig.add_trace(
            go.Scatter(
                x=times,
                y=buzz_scores,
                mode='lines',
                name='バズスコア',
                line=dict(color='#ff6b6b', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 107, 107, 0.2)'
            ),
            row=1, col=1
        )
        
        # センチメントスコア
        fig.add_trace(
            go.Scatter(
                x=times,
                y=sentiment_scores,
                mode='lines',
                name='センチメント',
                line=dict(color='#4ecdc4', width=2),
                fill='tozeroy',
                fillcolor='rgba(78, 205, 196, 0.2)'
            ),
            row=2, col=1
        )
        
        fig.update_layout(
            height=400,
            showlegend=True,
            hovermode='x unified',
            template='plotly_white'
        )
        
        return fig
    
    def get_trending_keywords(self) -> List[tuple]:
        """トレンドキーワード取得"""
        keywords = [
            ("ビタミンC", 0.89),
            ("レチノール", 0.85),
            ("ナイアシンアミド", 0.78),
            ("セラミド", 0.75),
            ("ヒアルロン酸", 0.72),
            ("CICA", 0.70),
            ("CBD", 0.68),
            ("ペプチド", 0.65),
            ("アルブチン", 0.62),
            ("コラーゲン", 0.60)
        ]
        # ランダムにスコアを少し変動させる
        return [(k, min(1.0, s + np.random.uniform(-0.05, 0.05))) for k, s in keywords]
    
    def render_market_analysis(self):
        """市場分析セクション"""
        st.markdown("### 📈 市場分析")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "カテゴリ別トレンド",
            "競合分析",
            "価格帯分析",
            "成分トレンド"
        ])
        
        with tab1:
            self.render_category_trends()
        
        with tab2:
            self.render_competitor_analysis()
        
        with tab3:
            self.render_price_analysis()
        
        with tab4:
            self.render_ingredient_trends()
    
    def render_category_trends(self):
        """カテゴリ別トレンド表示"""
        trends = st.session_state.market_trends
        
        fig = px.line(
            trends,
            x='date',
            y='trend_score',
            color='category',
            title='カテゴリ別トレンドスコア推移',
            labels={'trend_score': 'トレンドスコア', 'date': '日付', 'category': 'カテゴリ'}
        )
        
        fig.update_layout(
            hovermode='x unified',
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # カテゴリ別サマリー
        col1, col2, col3, col4 = st.columns(4)
        categories = trends['category'].unique()
        
        for i, (col, category) in enumerate(zip([col1, col2, col3, col4], categories)):
            with col:
                cat_data = trends[trends['category'] == category]
                latest_score = cat_data.iloc[-1]['trend_score']
                change = latest_score - cat_data.iloc[-7]['trend_score']
                
                st.info(f"**{category}**")
                st.metric(
                    "現在スコア",
                    f"{latest_score:.1f}",
                    f"{change:+.1f}"
                )
    
    def render_competitor_analysis(self):
        """競合分析表示"""
        # モック競合データ
        competitors = pd.DataFrame({
            'ブランド': ['ブランドA', 'ブランドB', 'ブランドC', 'ブランドD', 'ブランドE'],
            '市場シェア': [25, 20, 18, 15, 12],
            '新製品数': [5, 8, 3, 6, 4],
            'バズスコア': [0.75, 0.82, 0.65, 0.78, 0.70],
            '平均価格': [5000, 8000, 3000, 6000, 4500]
        })
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 市場シェア円グラフ
            fig_pie = px.pie(
                competitors,
                values='市場シェア',
                names='ブランド',
                title='市場シェア分布'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # バズスコアvs新製品数
            fig_scatter = px.scatter(
                competitors,
                x='新製品数',
                y='バズスコア',
                size='市場シェア',
                text='ブランド',
                title='イノベーション vs 話題性'
            )
            fig_scatter.update_traces(textposition='top center')
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # 競合比較テーブル
        st.markdown("#### 競合比較")
        st.dataframe(
            competitors.style.highlight_max(axis=0, subset=['市場シェア', '新製品数', 'バズスコア']),
            use_container_width=True
        )
    
    def render_price_analysis(self):
        """価格帯分析表示"""
        # 価格帯別データ生成
        price_ranges = ['~3000円', '3000~5000円', '5000~10000円', '10000円~']
        success_rates = [0.35, 0.45, 0.62, 0.78]
        product_counts = [120, 85, 45, 20]
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 価格帯別成功率
            fig_bar = go.Figure(data=[
                go.Bar(
                    x=price_ranges,
                    y=success_rates,
                    text=[f'{r:.0%}' for r in success_rates],
                    textposition='auto',
                    marker_color=['#ff9999', '#ffcc99', '#99ccff', '#99ff99']
                )
            ])
            fig_bar.update_layout(
                title='価格帯別ヒット率',
                xaxis_title='価格帯',
                yaxis_title='ヒット率',
                template='plotly_white'
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with col2:
            # 価格帯別製品数
            fig_pie = px.pie(
                values=product_counts,
                names=price_ranges,
                title='価格帯別製品分布',
                hole=0.3
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # インサイト
        st.info("""
        **価格戦略インサイト:**
        - 高価格帯（10000円以上）の製品がヒット率78%と最も高い
        - 中価格帯（5000~10000円）も62%と良好なパフォーマンス
        - 低価格帯は競争激化により成功率が低下傾向
        """)
    
    def render_ingredient_trends(self):
        """成分トレンド表示"""
        # トレンド成分データ
        ingredients = pd.DataFrame({
            '成分': ['ビタミンC', 'レチノール', 'ナイアシンアミド', 'ヒアルロン酸', 
                    'セラミド', 'ペプチド', 'AHA/BHA', 'CBD'],
            '検索トレンド': [95, 88, 82, 78, 75, 70, 65, 60],
            '論文数': [120, 98, 85, 110, 92, 78, 65, 45],
            '新製品採用率': [0.65, 0.58, 0.52, 0.48, 0.45, 0.38, 0.35, 0.28]
        })
        
        # レーダーチャート用データ準備
        categories = ['検索トレンド', '論文数', '新製品採用率']
        
        fig = go.Figure()
        
        # 上位3成分のレーダーチャート
        for i, row in ingredients.head(3).iterrows():
            values = [
                row['検索トレンド'] / 100,
                row['論文数'] / 150,
                row['新製品採用率']
            ]
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=row['成分']
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )
            ),
            showlegend=True,
            title='注目成分の多角的分析'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # トレンドテーブル
        st.markdown("#### 成分トレンド一覧")
        st.dataframe(
            ingredients.style.background_gradient(cmap='YlOrRd', subset=['検索トレンド', '論文数', '新製品採用率']),
            use_container_width=True
        )
    
    def render_prediction_panel(self):
        """予測パネル"""
        st.markdown("### 🎯 製品予測パネル")
        
        with st.expander("新規製品の予測を実行", expanded=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                product_name = st.text_input("製品名", placeholder="例: プレミアムビタミンCセラム")
                keywords = st.text_input("キーワード（カンマ区切り）", placeholder="例: ビタミンC, 美白, エイジングケア")
                price = st.number_input("価格（円）", min_value=1000, max_value=50000, value=5000, step=500)
            
            with col2:
                brand_strength = st.slider("ブランド力", 0.0, 1.0, 0.5, 0.05)
                ingredient_novelty = st.slider("成分の新規性", 0.0, 1.0, 0.5, 0.05)
                market_saturation = st.slider("市場飽和度", 0.0, 1.0, 0.3, 0.05)
            
            with col3:
                st.markdown("　")  # スペース調整
                if st.button("🚀 予測実行", use_container_width=True, type="primary"):
                    self.execute_prediction(
                        product_name, keywords, price,
                        brand_strength, ingredient_novelty, market_saturation
                    )
        
        # 予測履歴
        if st.session_state.prediction_history:
            st.markdown("#### 📋 最近の予測結果")
            
            for pred in st.session_state.prediction_history[-3:]:
                prob = pred['probability']
                if prob > 0.7:
                    box_class = "high-prob"
                    icon = "✅"
                elif prob > 0.4:
                    box_class = "medium-prob"
                    icon = "⚠️"
                else:
                    box_class = "low-prob"
                    icon = "❌"
                
                st.markdown(f"""
                <div class="prediction-box {box_class}">
                    <h4>{icon} {pred['name']}</h4>
                    <p>ヒット確率: <strong>{prob:.1%}</strong> | 
                    リスクレベル: {pred['risk']} | 
                    予測時刻: {pred['timestamp']}</p>
                </div>
                """, unsafe_allow_html=True)
    
    def execute_prediction(self, product_name, keywords, price,
                         brand_strength, ingredient_novelty, market_saturation):
        """予測実行"""
        with st.spinner("予測を実行中..."):
            # モック予測結果
            probability = np.random.uniform(0.3, 0.9)
            confidence = np.random.uniform(0.7, 0.95)
            risk_level = "低" if probability > 0.7 else "中" if probability > 0.4 else "高"
            
            # 結果を履歴に追加
            prediction = {
                'name': product_name,
                'probability': probability,
                'confidence': confidence,
                'risk': risk_level,
                'timestamp': datetime.now().strftime("%H:%M:%S")
            }
            st.session_state.prediction_history.append(prediction)
            
            # 結果表示
            st.success("予測が完了しました！")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("ヒット確率", f"{probability:.1%}")
            with col2:
                st.metric("信頼度", f"{confidence:.1%}")
            with col3:
                st.metric("リスクレベル", risk_level)
            
            # 推奨アクション
            if probability > 0.7:
                st.info("💡 **推奨アクション**: 積極的な市場投入を推奨。マーケティング予算の増額を検討。")
            elif probability > 0.4:
                st.warning("💡 **推奨アクション**: 慎重な市場投入を推奨。テストマーケティングから開始。")
            else:
                st.error("💡 **推奨アクション**: 製品改良の検討を推奨。成分やマーケティング戦略の見直し。")
    
    def render_alerts_section(self):
        """アラートセクション"""
        st.markdown("### 🔔 アラート & 通知")
        
        # モックアラートデータ
        alerts = [
            {
                'type': 'success',
                'title': '新トレンド検出',
                'message': 'CBD成分の検索数が前週比150%増加',
                'time': '5分前'
            },
            {
                'type': 'warning',
                'title': '競合動向',
                'message': 'ブランドAが新製品を3つ同時リリース',
                'time': '1時間前'
            },
            {
                'type': 'info',
                'title': 'モデル更新',
                'message': '予測モデルの自動再学習が完了（精度 +2.3%）',
                'time': '3時間前'
            }
        ]
        
        for alert in alerts:
            if alert['type'] == 'success':
                st.success(f"🟢 **{alert['title']}** - {alert['message']} ({alert['time']})")
            elif alert['type'] == 'warning':
                st.warning(f"🟡 **{alert['title']}** - {alert['message']} ({alert['time']})")
            else:
                st.info(f"🔵 **{alert['title']}** - {alert['message']} ({alert['time']})")
    
    def update_data(self):
        """データ更新"""
        with st.spinner("データを更新中..."):
            # マーケットトレンドの更新
            st.session_state.market_trends = self.generate_mock_trends()
            
            # モデルパフォーマンスの更新
            st.session_state.model_performance = self.generate_mock_performance()
            
            # 完了メッセージ
            st.success("データが正常に更新されました！")
            time.sleep(1)
            st.rerun()
    
    def render_sidebar(self):
        """サイドバーのレンダリング"""
        with st.sidebar:
            st.markdown("## ⚙️ ダッシュボード設定")
            
            # 自動更新設定
            st.markdown("### 自動更新")
            auto_refresh = st.checkbox(
                "自動更新を有効化",
                value=st.session_state.auto_refresh
            )
            st.session_state.auto_refresh = auto_refresh
            
            if auto_refresh:
                refresh_interval = st.select_slider(
                    "更新間隔",
                    options=[30, 60, 120, 300, 600],
                    format_func=lambda x: f"{x}秒" if x < 60 else f"{x//60}分",
                    value=60
                )
            
            st.markdown("---")
            
            # フィルター設定
            st.markdown("### 📊 表示フィルター")
            
            show_categories = st.multiselect(
                "表示カテゴリ",
                ['スキンケア', 'メイクアップ', 'ヘアケア', 'フレグランス'],
                default=['スキンケア', 'メイクアップ']
            )
            
            date_range = st.select_slider(
                "データ期間",
                options=[7, 14, 30, 60, 90],
                format_func=lambda x: f"{x}日間",
                value=30
            )
            
            st.markdown("---")
            
            # エクスポート機能
            st.markdown("### 💾 データエクスポート")
            
            if st.button("📥 レポート生成", use_container_width=True):
                self.generate_report()
            
            if st.button("📊 データダウンロード", use_container_width=True):
                self.download_data()
            
            st.markdown("---")
            
            # システム情報
            st.markdown("### ℹ️ システム情報")
            st.info(f"""
            **バージョン**: 3.0.0  
            **最終更新**: {datetime.now().strftime('%Y-%m-%d')}  
            **稼働状態**: 🟢 正常
            """)
    
    def generate_report(self):
        """レポート生成"""
        with st.spinner("レポートを生成中..."):
            time.sleep(2)
            st.success("レポートが生成されました！")
            st.download_button(
                label="📄 PDFダウンロード",
                data=b"Mock PDF content",
                file_name=f"report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
    
    def download_data(self):
        """データダウンロード"""
        # CSVデータ準備
        df = st.session_state.market_trends
        csv = df.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📊 CSVダウンロード",
            data=csv,
            file_name=f"market_trends_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    def run(self):
        """ダッシュボード実行"""
        # サイドバー
        self.render_sidebar()
        
        # メインコンテンツ
        self.render_header()
        
        st.markdown("---")
        self.render_metrics_row()
        
        st.markdown("---")
        self.render_real_time_monitor()
        
        st.markdown("---")
        self.render_market_analysis()
        
        st.markdown("---")
        self.render_prediction_panel()
        
        st.markdown("---")
        self.render_alerts_section()
        
        # 自動更新
        if st.session_state.auto_refresh:
            time.sleep(1)
            st.rerun()


def main():
    """メイン実行関数"""
    dashboard = DashboardManager()
    dashboard.run()


if __name__ == "__main__":
    main()