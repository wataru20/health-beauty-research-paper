#!/usr/bin/env python
"""
Streamlit Web UI
AIヒット予測システムのインタラクティブなWebインターフェース
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os
import sys
import json
import joblib
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.basic_model import HitPredictionModel
from src.preprocessing.data_pipeline import DataPipeline
from src.preprocessing.feature_engineering import FeatureEngineer
from src.analysis.model_explainer import ModelExplainer, InteractivePlotter
from src.data_collection.news_collector import NewsCollector
from src.data_collection.academic_collector import AcademicPaperCollector

# ページ設定
st.set_page_config(
    page_title="🎯 AIヒット予測システム",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main {padding: 0rem 0rem;}
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        margin: 5px;
    }
    .prediction-high {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .prediction-medium {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .prediction-low {
        background-color: #f8d7da;
        color: #721c24;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# セッション状態の初期化
def init_session_state():
    """セッション状態を初期化"""
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = DataPipeline()
    if 'engineer' not in st.session_state:
        st.session_state.engineer = FeatureEngineer()
    if 'prediction_history' not in st.session_state:
        st.session_state.prediction_history = []
    if 'current_features' not in st.session_state:
        st.session_state.current_features = None
    if 'current_prediction' not in st.session_state:
        st.session_state.current_prediction = None


@st.cache_resource
def load_model():
    """モデルを読み込み（キャッシュ付き）"""
    model_dir = Path("data/models")
    
    # 最新のモデルファイルを探す
    model_files = list(model_dir.glob("*.pkl"))
    
    if model_files:
        # 最新のモデルを選択
        latest_model = max(model_files, key=os.path.getctime)
        
        # モデル読み込み
        model = HitPredictionModel()
        model.load_model(str(latest_model))
        
        return model, str(latest_model)
    else:
        # モデルがない場合はダミーモデルを作成
        st.warning("学習済みモデルが見つかりません。ダミーモデルを使用します。")
        model = HitPredictionModel()
        
        # ダミーデータで簡易学習
        dummy_data = pd.DataFrame({
            'id': range(100)
        })
        X_dummy = model.prepare_features(dummy_data)
        y_dummy = np.random.choice([0, 1], 100)
        model.train(X_dummy, y_dummy, validate=False)
        
        return model, "dummy_model"


def sidebar_inputs():
    """サイドバーの入力フォーム"""
    st.sidebar.header("📝 製品情報入力")
    
    with st.sidebar.form("product_form"):
        # 基本情報
        st.subheader("基本情報")
        product_name = st.text_input("製品名", value="新製品サンプル")
        
        # カテゴリ選択
        category = st.selectbox(
            "カテゴリ",
            ["スキンケア", "メイクアップ", "ヘアケア", "ボディケア", "フレグランス"]
        )
        
        # 主要成分
        st.subheader("主要成分")
        ingredients = st.multiselect(
            "含有成分を選択",
            ["ビタミンC", "レチノール", "ヒアルロン酸", "ナイアシンアミド", 
             "ペプチド", "セラミド", "コラーゲン", "その他"],
            default=["ビタミンC"]
        )
        
        # 価格設定
        st.subheader("価格設定")
        price = st.slider(
            "価格（円）",
            min_value=1000,
            max_value=50000,
            value=5000,
            step=500
        )
        
        # マーケティング要素
        st.subheader("マーケティング要素")
        
        brand_strength = st.slider(
            "ブランド力",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="0: 新規ブランド, 1: 確立されたブランド"
        )
        
        ingredient_novelty = st.slider(
            "成分の新規性",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="0: 一般的な成分, 1: 革新的な成分"
        )
        
        # 市場環境
        st.subheader("市場環境")
        
        competitor_count = st.number_input(
            "競合製品数",
            min_value=0,
            max_value=100,
            value=10
        )
        
        market_saturation = st.slider(
            "市場飽和度",
            min_value=0.0,
            max_value=1.0,
            value=0.5,
            step=0.1,
            help="0: 新規市場, 1: 飽和市場"
        )
        
        # 予測実行ボタン
        submitted = st.form_submit_button("🔮 予測を実行", use_container_width=True)
        
    return {
        'submitted': submitted,
        'product_info': {
            'name': product_name,
            'category': category,
            'keywords': ingredients,
            'price': price,
            'brand_strength': brand_strength,
            'ingredient_novelty': ingredient_novelty,
            'competitor_count': competitor_count,
            'market_saturation': market_saturation,
            'seasonality_factor': 0.5  # デフォルト値
        }
    }


def display_prediction_results(prediction_result, product_name):
    """予測結果を表示"""
    st.header("📊 予測結果")
    
    # メトリクス表示
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        hit_prob = prediction_result['hit_probability'].iloc[0]
        delta = hit_prob - 0.5
        st.metric(
            "ヒット確率",
            f"{hit_prob:.1%}",
            f"{delta:+.1%}",
            delta_color="normal" if delta > 0 else "inverse"
        )
    
    with col2:
        confidence = prediction_result['confidence'].iloc[0]
        st.metric(
            "予測信頼度",
            f"{confidence:.1%}",
            help="モデルの予測の確信度"
        )
    
    with col3:
        risk_level = prediction_result['risk_level'].iloc[0]
        risk_emoji = {
            'High Risk': '🔴',
            'Medium Risk': '🟡',
            'Medium Potential': '🟢',
            'High Potential': '🎯'
        }
        st.metric(
            "リスクレベル",
            f"{risk_emoji.get(risk_level, '❓')} {risk_level}"
        )
    
    with col4:
        prediction_label = "ヒット" if prediction_result['prediction'].iloc[0] == 1 else "非ヒット"
        st.metric(
            "予測判定",
            prediction_label
        )
    
    # 詳細な分析結果
    st.subheader("🎯 予測の確信度")
    
    # ゲージチャート
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=hit_prob * 100,
        title={'text': f"{product_name}のヒット確率"},
        delta={'reference': 50, 'increasing': {'color': "green"}},
        gauge={
            'axis': {'range': [None, 100]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 30], 'color': "lightgray"},
                {'range': [30, 70], 'color': "gray"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        }
    ))
    
    fig_gauge.update_layout(height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)


def display_shap_analysis(model, features, product_name):
    """SHAP分析結果を表示"""
    st.header("🔍 予測根拠の詳細分析（SHAP）")
    
    try:
        # ModelExplainer初期化
        explainer = ModelExplainer(
            model.model,
            feature_names=features.columns.tolist(),
            background_data=features  # 単一サンプルを背景データとして使用
        )
        
        # タブ作成
        tab1, tab2, tab3 = st.tabs(["📊 寄与度分析", "📈 要因の詳細", "💡 改善提案"])
        
        with tab1:
            st.subheader("各特徴量の予測への寄与度")
            
            # ウォーターフォールプロット
            waterfall_data = explainer.create_waterfall_plot(features)
            fig_waterfall = InteractivePlotter.create_waterfall_plot(waterfall_data)
            st.plotly_chart(fig_waterfall, use_container_width=True)
            
            # 説明
            st.info(
                "📌 **グラフの読み方**\n"
                "- 緑のバー: ヒット確率を上げる要因\n"
                "- 赤のバー: ヒット確率を下げる要因\n"
                "- Base: 平均的な予測値\n"
                "- Prediction: 最終的な予測値"
            )
        
        with tab2:
            st.subheader("ポジティブ/ネガティブ要因")
            
            # フォースプロットデータ
            force_data = explainer.create_force_plot_data(features)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**✅ ポジティブ要因（TOP 5）**")
                for factor in force_data['positive_features'][:5]:
                    st.write(f"- {factor['feature']}: +{factor['value']:.3f}")
            
            with col2:
                st.write("**❌ ネガティブ要因（TOP 5）**")
                for factor in force_data['negative_features'][:5]:
                    st.write(f"- {factor['feature']}: {factor['value']:.3f}")
            
            # フォースプロット
            fig_force = InteractivePlotter.create_force_plot(force_data)
            st.plotly_chart(fig_force, use_container_width=True)
        
        with tab3:
            st.subheader("📋 改善提案")
            
            # 説明レポート生成
            report = explainer.generate_explanation_report(features, product_name)
            
            # リスクレベル表示
            risk_color = report['prediction']['risk_color']
            risk_level = report['prediction']['risk_level']
            
            if risk_color == "success":
                st.success(f"🎯 {risk_level}")
            elif risk_color == "warning":
                st.warning(f"⚠️ {risk_level}")
            else:
                st.error(f"🔴 {risk_level}")
            
            # 推奨事項
            st.write("**推奨アクション:**")
            for recommendation in report['recommendations']:
                st.write(f"• {recommendation}")
            
    except Exception as e:
        st.error(f"SHAP分析でエラーが発生しました: {str(e)}")
        st.info("モデルの再学習が必要な可能性があります。")


def display_trend_analysis():
    """トレンド分析を表示"""
    st.header("📈 市場トレンド分析")
    
    # ダミーデータでトレンドグラフを作成
    dates = pd.date_range(start='2024-01-01', periods=90, freq='D')
    
    trend_data = pd.DataFrame({
        'date': dates,
        'vitamin_c': np.cumsum(np.random.randn(90)) + 50,
        'retinol': np.cumsum(np.random.randn(90)) + 45,
        'hyaluronic_acid': np.cumsum(np.random.randn(90)) + 40,
        'niacinamide': np.cumsum(np.random.randn(90)) + 55
    })
    
    # プロット作成
    fig = px.line(
        trend_data.melt(id_vars=['date'], var_name='ingredient', value_name='trend_score'),
        x='date',
        y='trend_score',
        color='ingredient',
        title='成分別トレンドスコアの推移（過去90日）',
        labels={'trend_score': 'トレンドスコア', 'date': '日付', 'ingredient': '成分'}
    )
    
    fig.update_layout(hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)
    
    # トレンドサマリー
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🔥 最もホットな成分", "ナイアシンアミド", "+15%")
    
    with col2:
        st.metric("📰 今週の話題記事数", "234", "+45")
    
    with col3:
        st.metric("🔬 新規研究論文", "12", "+3")


def display_history():
    """予測履歴を表示"""
    st.header("📜 予測履歴")
    
    if st.session_state.prediction_history:
        # 履歴をDataFrameに変換
        history_df = pd.DataFrame(st.session_state.prediction_history)
        
        # 表示用に整形
        display_df = history_df[['timestamp', 'product_name', 'hit_probability', 'risk_level']]
        display_df['hit_probability'] = display_df['hit_probability'].apply(lambda x: f"{x:.1%}")
        display_df.columns = ['予測日時', '製品名', 'ヒット確率', 'リスクレベル']
        
        # テーブル表示
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # CSVダウンロードボタン
        csv = history_df.to_csv(index=False)
        st.download_button(
            label="📥 履歴をCSVでダウンロード",
            data=csv,
            file_name=f"prediction_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("まだ予測履歴がありません。製品情報を入力して予測を実行してください。")


def main():
    """メインアプリケーション"""
    
    # 初期化
    init_session_state()
    
    # タイトル
    st.title("🎯 AIヒット予測システム")
    st.markdown("### 新製品のヒット確率をAIで予測し、成功要因を分析します")
    
    # モデル読み込み
    if st.session_state.model is None:
        with st.spinner("モデルを読み込み中..."):
            model, model_path = load_model()
            st.session_state.model = model
            st.success(f"✅ モデル読み込み完了: {os.path.basename(model_path)}")
    
    # サイドバー入力
    input_data = sidebar_inputs()
    
    # メインエリア
    if input_data['submitted']:
        with st.spinner("予測を実行中..."):
            # 特徴量抽出
            features = st.session_state.pipeline.extract_features(input_data['product_info'])
            
            # 特徴量エンジニアリング
            enhanced_features = st.session_state.engineer.create_advanced_features(features)
            
            # 予測実行
            prediction_result = st.session_state.model.predict_with_confidence(enhanced_features)
            
            # セッション状態に保存
            st.session_state.current_features = enhanced_features
            st.session_state.current_prediction = prediction_result
            
            # 履歴に追加
            st.session_state.prediction_history.append({
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'product_name': input_data['product_info']['name'],
                'hit_probability': prediction_result['hit_probability'].iloc[0],
                'confidence': prediction_result['confidence'].iloc[0],
                'risk_level': prediction_result['risk_level'].iloc[0],
                'prediction': prediction_result['prediction'].iloc[0]
            })
            
            # 成功メッセージ
            st.success("✅ 予測が完了しました！")
    
    # 結果表示エリア
    if st.session_state.current_prediction is not None:
        # 予測結果
        display_prediction_results(
            st.session_state.current_prediction,
            st.session_state.prediction_history[-1]['product_name'] if st.session_state.prediction_history else "製品"
        )
        
        # SHAP分析
        display_shap_analysis(
            st.session_state.model,
            st.session_state.current_features,
            st.session_state.prediction_history[-1]['product_name'] if st.session_state.prediction_history else "製品"
        )
        
        # タブでその他の情報を表示
        tab1, tab2 = st.tabs(["📈 市場トレンド", "📜 予測履歴"])
        
        with tab1:
            display_trend_analysis()
        
        with tab2:
            display_history()
    
    else:
        # 初期画面
        st.info("👈 左のサイドバーから製品情報を入力して、予測を開始してください。")
        
        # 使い方
        with st.expander("📖 使い方"):
            st.markdown("""
            1. **製品情報の入力**: 左のサイドバーで製品の詳細情報を入力します
            2. **予測の実行**: 「予測を実行」ボタンをクリックします
            3. **結果の確認**: ヒット確率と詳細な分析結果が表示されます
            4. **改善点の把握**: SHAP分析により、改善すべき要因が明確になります
            
            ### 評価指標の説明
            - **ヒット確率**: AIが予測する製品の成功確率
            - **予測信頼度**: モデルの予測に対する確信度
            - **リスクレベル**: 総合的なリスク評価
            """)
        
        # システム情報
        with st.expander("ℹ️ システム情報"):
            st.markdown("""
            - **バージョン**: Phase 3 (SHAP + WebUI)
            - **モデル**: ランダムフォレスト
            - **特徴量数**: 30+
            - **データソース**: 学術論文、ニュース、ソーシャルメディア
            """)


if __name__ == "__main__":
    main()