import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# 簡易版の相関分析クラス
class SimpleCorrelationAnalyzer:
    def __init__(self):
        self.weights = {
            'rank_correlation': 0.3,
            'time_series': 0.5,
            'category': 0.2
        }
    
    def calculate_correlation(self, data1, data2):
        if len(data1) != len(data2):
            return 0
        return np.corrcoef(data1, data2)[0, 1]
    
    def calculate_prediction_score(self, rank_corr, time_corr, category_score):
        score = (self.weights['rank_correlation'] * rank_corr +
                self.weights['time_series'] * time_corr +
                self.weights['category'] * category_score)
        
        confidence = "高い" if score > 0.6 else "中程度" if score > 0.4 else "低い"
        
        return {
            'score': score,
            'confidence': confidence,
            'recommendation': self.get_recommendation(score)
        }
    
    def get_recommendation(self, score):
        if score >= 0.7:
            return "即座に日本市場投入を推奨"
        elif score >= 0.5:
            return "市場テストを実施後、投入検討"
        else:
            return "追加分析が必要"

# アプリケーション設定
st.set_page_config(
    page_title="韓国コスメヒット予測システム",
    page_icon="💄",
    layout="wide"
)

st.title("💄 韓国コスメヒット予測システム")
st.markdown("韓国市場のトレンドから日本市場でのヒット可能性を予測します")

# サイドバー
with st.sidebar:
    st.header("📊 分析設定")
    
    analysis_type = st.selectbox(
        "分析タイプ",
        ["簡易分析", "詳細分析", "SNS統合分析"]
    )
    
    max_lag = st.slider(
        "最大ラグ期間（月）",
        min_value=1,
        max_value=12,
        value=6
    )
    
    correlation_threshold = st.slider(
        "相関係数閾値",
        min_value=0.3,
        max_value=0.9,
        value=0.6,
        step=0.1
    )

# サンプルデータ生成
@st.cache_data
def load_sample_data():
    np.random.seed(42)
    dates = pd.date_range('2024-01', periods=12, freq='M')
    
    products = ['CICA クリーム', 'スネイルエッセンス', 'ビタミンCセラム', 
                'ティーツリートナー', 'セラミドクリーム']
    categories = ['スキンケア', 'スキンケア', 'セラム', 'トナー', 'クリーム']
    
    data = []
    for i, product in enumerate(products):
        korea_sales = np.random.uniform(3000, 8000, 12) * (1 + i * 0.1)
        japan_sales = np.random.uniform(2000, 6000, 12) * (1 + i * 0.08)
        
        for j, date in enumerate(dates):
            data.append({
                'date': date,
                'product': product,
                'category': categories[i],
                'korea_sales': korea_sales[j],
                'japan_sales': japan_sales[j],
                'korea_rank': np.random.randint(1, 20),
                'japan_rank': np.random.randint(1, 25)
            })
    
    return pd.DataFrame(data)

# データ読み込み
df = load_sample_data()

# タブ作成
tab1, tab2, tab3 = st.tabs(["📈 ダッシュボード", "🔍 商品分析", "🎯 予測結果"])

with tab1:
    st.subheader("市場概要")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("分析商品数", f"{len(df['product'].unique())} 商品")
    
    with col2:
        st.metric("データ期間", f"{len(df['date'].unique())} ヶ月")
    
    with col3:
        avg_korea_sales = df['korea_sales'].mean()
        st.metric("韓国平均売上", f"¥{avg_korea_sales:,.0f}")
    
    with col4:
        avg_japan_sales = df['japan_sales'].mean()
        st.metric("日本平均売上", f"¥{avg_japan_sales:,.0f}")
    
    st.divider()
    
    # 売上推移グラフ
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("月次売上推移")
        monthly_data = df.groupby('date')[['korea_sales', 'japan_sales']].sum().reset_index()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=monthly_data['date'],
            y=monthly_data['korea_sales'],
            mode='lines+markers',
            name='韓国市場',
            line=dict(color='red', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=monthly_data['date'],
            y=monthly_data['japan_sales'],
            mode='lines+markers',
            name='日本市場',
            line=dict(color='blue', width=2)
        ))
        fig.update_layout(
            xaxis_title="期間",
            yaxis_title="売上高",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("カテゴリ別売上")
        category_data = df.groupby('category')[['korea_sales', 'japan_sales']].mean().reset_index()
        category_data_melted = pd.melt(category_data, id_vars=['category'], 
                                       value_vars=['korea_sales', 'japan_sales'],
                                       var_name='market', value_name='sales')
        category_data_melted['market'] = category_data_melted['market'].map(
            {'korea_sales': '韓国', 'japan_sales': '日本'}
        )
        
        fig = px.bar(
            category_data_melted,
            x='category',
            y='sales',
            color='market',
            barmode='group',
            color_discrete_map={'韓国': 'red', '日本': 'blue'},
            height=350
        )
        fig.update_layout(
            xaxis_title="カテゴリ",
            yaxis_title="平均売上高",
            legend_title="市場"
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("商品別詳細分析")
    
    selected_product = st.selectbox(
        "分析対象商品を選択",
        df['product'].unique()
    )
    
    product_data = df[df['product'] == selected_product]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 商品別売上推移
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=product_data['date'],
            y=product_data['korea_sales'],
            mode='lines+markers',
            name='韓国市場',
            line=dict(color='red', width=2)
        ))
        fig.add_trace(go.Scatter(
            x=product_data['date'],
            y=product_data['japan_sales'],
            mode='lines+markers',
            name='日本市場',
            line=dict(color='blue', width=2)
        ))
        fig.update_layout(
            title=f"{selected_product} - 売上推移",
            xaxis_title="期間",
            yaxis_title="売上高",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 相関分析結果")
        
        analyzer = SimpleCorrelationAnalyzer()
        
        # 相関係数計算
        sales_corr = analyzer.calculate_correlation(
            product_data['korea_sales'].values,
            product_data['japan_sales'].values
        )
        
        rank_corr = analyzer.calculate_correlation(
            product_data['korea_rank'].values,
            product_data['japan_rank'].values
        )
        
        st.metric("売上相関係数", f"{sales_corr:.3f}")
        st.metric("順位相関係数", f"{rank_corr:.3f}")
        
        if sales_corr > correlation_threshold:
            st.success(f"✅ 高い相関性あり")
        elif sales_corr > 0.4:
            st.warning(f"⚠️ 中程度の相関性")
        else:
            st.error(f"❌ 相関性が低い")

with tab3:
    st.subheader("🎯 ヒット予測結果")
    
    analyzer = SimpleCorrelationAnalyzer()
    predictions = []
    
    for product in df['product'].unique():
        product_data = df[df['product'] == product]
        
        # 各種相関係数を計算
        sales_corr = analyzer.calculate_correlation(
            product_data['korea_sales'].values,
            product_data['japan_sales'].values
        )
        
        rank_corr = analyzer.calculate_correlation(
            product_data['korea_rank'].values,
            product_data['japan_rank'].values
        )
        
        # カテゴリスコア（簡易版）
        category_score = 0.8 if product_data['category'].iloc[0] == 'スキンケア' else 0.6
        
        # 予測スコア計算
        prediction = analyzer.calculate_prediction_score(
            abs(rank_corr),
            sales_corr,
            category_score
        )
        
        predictions.append({
            '商品名': product,
            'カテゴリ': product_data['category'].iloc[0],
            '予測スコア': prediction['score'],
            '信頼度': prediction['confidence'],
            '推奨アクション': prediction['recommendation']
        })
    
    predictions_df = pd.DataFrame(predictions)
    predictions_df = predictions_df.sort_values('予測スコア', ascending=False)
    
    # 結果表示
    st.dataframe(
        predictions_df,
        use_container_width=True,
        height=300
    )
    
    # サマリー
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        high_potential = len(predictions_df[predictions_df['予測スコア'] >= 0.7])
        st.metric("高ポテンシャル", f"{high_potential} 商品")
    
    with col2:
        medium_potential = len(predictions_df[(predictions_df['予測スコア'] >= 0.4) & 
                                            (predictions_df['予測スコア'] < 0.7)])
        st.metric("中ポテンシャル", f"{medium_potential} 商品")
    
    with col3:
        low_potential = len(predictions_df[predictions_df['予測スコア'] < 0.4])
        st.metric("低ポテンシャル", f"{low_potential} 商品")
    
    # ダウンロードボタン
    st.divider()
    csv = predictions_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 予測結果をCSVでダウンロード",
        data=csv,
        file_name=f"prediction_results_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )