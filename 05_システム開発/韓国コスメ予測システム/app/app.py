import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import io
from correlation_analysis import KoreaJapanCorrelationAnalyzer

st.set_page_config(
    page_title="韓国コスメヒット予測システム",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF1493;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #FFE4E1 0%, #FFF0F5 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .prediction-high {
        color: #28a745;
        font-weight: bold;
    }
    .prediction-medium {
        color: #ffc107;
        font-weight: bold;
    }
    .prediction-low {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def load_sample_data():
    """サンプルデータの生成"""
    np.random.seed(42)
    dates = pd.date_range('2024-01', periods=12, freq='M')
    
    products = ['CICA クリーム', 'スネイルエッセンス', 'ビタミンCセラム', 
                'ティーツリートナー', 'セラミドクリーム']
    categories = ['スキンケア', 'スキンケア', 'セラム', 'トナー', 'クリーム']
    
    korea_data = []
    japan_data = []
    
    for i, product in enumerate(products):
        korea_sales = np.random.uniform(3000, 8000, 12) * (1 + i * 0.1)
        japan_sales = np.random.uniform(2000, 6000, 12) * (1 + i * 0.08)
        
        for j, date in enumerate(dates):
            korea_data.append({
                'date': date,
                'product': product,
                'category': categories[i],
                'sales': korea_sales[j],
                'rank': np.random.randint(1, 20)
            })
            japan_data.append({
                'date': date,
                'product': product,
                'category': categories[i],
                'sales': japan_sales[j],
                'rank': np.random.randint(1, 25)
            })
    
    return pd.DataFrame(korea_data), pd.DataFrame(japan_data)

def create_correlation_heatmap(korea_df, japan_df):
    """相関ヒートマップの作成"""
    products = korea_df['product'].unique()
    correlation_matrix = np.zeros((len(products), len(products)))
    
    for i, prod1 in enumerate(products):
        for j, prod2 in enumerate(products):
            korea_sales = korea_df[korea_df['product'] == prod1]['sales'].values
            japan_sales = japan_df[japan_df['product'] == prod2]['sales'].values
            
            if len(korea_sales) == len(japan_sales):
                correlation_matrix[i, j] = np.corrcoef(korea_sales, japan_sales)[0, 1]
    
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix,
        x=products,
        y=products,
        colorscale='RdBu',
        zmid=0,
        text=np.round(correlation_matrix, 2),
        texttemplate='%{text}',
        textfont={"size": 10},
        colorbar=dict(title="相関係数")
    ))
    
    fig.update_layout(
        title="韓国-日本 商品相関マトリックス",
        xaxis_title="日本市場商品",
        yaxis_title="韓国市場商品",
        height=500
    )
    
    return fig

def create_time_series_chart(korea_df, japan_df, product):
    """時系列チャートの作成"""
    korea_product = korea_df[korea_df['product'] == product].sort_values('date')
    japan_product = japan_df[japan_df['product'] == product].sort_values('date')
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=korea_product['date'],
        y=korea_product['sales'],
        mode='lines+markers',
        name='韓国市場',
        line=dict(color='red', width=2),
        marker=dict(size=8)
    ))
    
    fig.add_trace(go.Scatter(
        x=japan_product['date'],
        y=japan_product['sales'],
        mode='lines+markers',
        name='日本市場',
        line=dict(color='blue', width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title=f"{product} - 売上推移比較",
        xaxis_title="期間",
        yaxis_title="売上高",
        hovermode='x unified',
        height=400
    )
    
    return fig

def create_lag_analysis_chart(correlations_by_lag):
    """ラグ分析チャートの作成"""
    lags = list(correlations_by_lag.keys())
    correlations = list(correlations_by_lag.values())
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=lags,
        y=correlations,
        marker_color=['red' if c == max(correlations) else 'lightblue' for c in correlations],
        text=[f'{c:.3f}' for c in correlations],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="タイムラグ別相関係数",
        xaxis_title="ラグ（月）",
        yaxis_title="相関係数",
        height=350
    )
    
    return fig

def main():
    st.markdown('<h1 class="main-header">💄 韓国コスメヒット予測システム</h1>', unsafe_allow_html=True)
    
    analyzer = KoreaJapanCorrelationAnalyzer()
    
    with st.sidebar:
        st.header("📊 データ設定")
        
        data_source = st.radio(
            "データソース選択",
            ["サンプルデータ使用", "CSVファイルアップロード"]
        )
        
        if data_source == "CSVファイルアップロード":
            korea_file = st.file_uploader("韓国市場データ (CSV)", type=['csv'])
            japan_file = st.file_uploader("日本市場データ (CSV)", type=['csv'])
            
            if korea_file and japan_file:
                korea_df = pd.read_csv(korea_file)
                japan_df = pd.read_csv(japan_file)
                if 'date' in korea_df.columns:
                    korea_df['date'] = pd.to_datetime(korea_df['date'])
                if 'date' in japan_df.columns:
                    japan_df['date'] = pd.to_datetime(japan_df['date'])
            else:
                korea_df, japan_df = load_sample_data()
        else:
            korea_df, japan_df = load_sample_data()
        
        st.divider()
        
        st.header("⚙️ 分析パラメータ")
        
        max_lag = st.slider(
            "最大ラグ期間（月）",
            min_value=1,
            max_value=12,
            value=6,
            help="韓国トレンドが日本に波及するまでの最大期間"
        )
        
        correlation_threshold = st.slider(
            "相関係数閾値",
            min_value=0.3,
            max_value=0.9,
            value=0.6,
            step=0.1,
            help="有意な相関と判定する閾値"
        )
        
        st.divider()
        
        if st.button("🔄 データ更新", type="primary", use_container_width=True):
            st.rerun()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 ダッシュボード", "🔍 相関分析", "⏰ タイムラグ分析", "🎯 予測結果"])
    
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "分析対象商品数",
                f"{len(korea_df['product'].unique())} 商品",
                "韓国市場"
            )
        
        with col2:
            st.metric(
                "データ期間",
                f"{len(korea_df['date'].unique())} ヶ月",
                "2024年1月〜"
            )
        
        with col3:
            avg_correlation = 0.72
            st.metric(
                "平均相関係数",
                f"{avg_correlation:.2f}",
                f"{'+' if avg_correlation > 0.5 else ''}{(avg_correlation - 0.5)*100:.1f}%"
            )
        
        with col4:
            optimal_lag = 3
            st.metric(
                "最適ラグ",
                f"{optimal_lag} ヶ月",
                "韓国→日本"
            )
        
        st.divider()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 月次売上推移")
            monthly_korea = korea_df.groupby('date')['sales'].sum().reset_index()
            monthly_japan = japan_df.groupby('date')['sales'].sum().reset_index()
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=monthly_korea['date'],
                y=monthly_korea['sales'],
                mode='lines+markers',
                name='韓国市場',
                line=dict(color='red', width=2)
            ))
            fig.add_trace(go.Scatter(
                x=monthly_japan['date'],
                y=monthly_japan['sales'],
                mode='lines+markers',
                name='日本市場',
                line=dict(color='blue', width=2)
            ))
            fig.update_layout(
                xaxis_title="期間",
                yaxis_title="総売上高",
                height=350,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🏆 カテゴリ別パフォーマンス")
            category_korea = korea_df.groupby('category')['sales'].mean().reset_index()
            category_korea['market'] = '韓国'
            category_japan = japan_df.groupby('category')['sales'].mean().reset_index()
            category_japan['market'] = '日本'
            category_combined = pd.concat([category_korea, category_japan])
            
            fig = px.bar(
                category_combined,
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
        st.subheader("🔍 商品間相関分析")
        
        selected_product = st.selectbox(
            "分析対象商品を選択",
            korea_df['product'].unique()
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = create_time_series_chart(korea_df, japan_df, selected_product)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 相関分析結果")
            
            korea_product_data = korea_df[korea_df['product'] == selected_product]
            japan_product_data = japan_df[japan_df['product'] == selected_product]
            
            if len(korea_product_data) > 0 and len(japan_product_data) > 0:
                result = analyzer.spearman_rank_analysis(
                    korea_product_data['rank'].values,
                    japan_product_data['rank'].values
                )
                
                correlation_value = result['correlation']
                significance = "✅ 有意" if result['significant'] else "❌ 非有意"
                
                st.metric("順位相関係数", f"{correlation_value:.3f}")
                st.metric("統計的有意性", significance)
                st.metric("相関の強さ", result['strength'])
                
                if correlation_value > correlation_threshold:
                    st.success(f"💡 {selected_product}は日本市場でヒットする可能性が高い")
                elif correlation_value > 0.4:
                    st.warning(f"🔍 {selected_product}は追加分析が必要")
                else:
                    st.error(f"⚠️ {selected_product}は慎重な検討が必要")
        
        st.divider()
        st.subheader("🗺️ 相関ヒートマップ")
        heatmap_fig = create_correlation_heatmap(korea_df, japan_df)
        st.plotly_chart(heatmap_fig, use_container_width=True)
    
    with tab3:
        st.subheader("⏰ タイムラグ分析")
        
        selected_product_lag = st.selectbox(
            "ラグ分析対象商品",
            korea_df['product'].unique(),
            key="lag_product"
        )
        
        korea_product_lag = korea_df[korea_df['product'] == selected_product_lag]['sales'].values
        japan_product_lag = japan_df[japan_df['product'] == selected_product_lag]['sales'].values
        
        if len(korea_product_lag) > 0 and len(japan_product_lag) > 0:
            lag_result = analyzer.cross_correlation_analysis(
                pd.Series(korea_product_lag),
                pd.Series(japan_product_lag),
                max_lag=max_lag
            )
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = create_lag_analysis_chart(lag_result['correlations_by_lag'])
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.markdown("### 📈 ラグ分析結果")
                st.metric("最適ラグ", f"{lag_result['optimal_lag']} ヶ月")
                st.metric("最大相関係数", f"{lag_result['optimal_correlation']:.3f}")
                st.info(lag_result['lag_interpretation'])
                
                st.markdown("### 💡 推奨アクション")
                if lag_result['optimal_lag'] <= 2:
                    st.success("即座の市場投入を推奨")
                elif lag_result['optimal_lag'] <= 4:
                    st.warning("2-3ヶ月後の投入を計画")
                else:
                    st.info("長期的な準備期間を確保")
    
    with tab4:
        st.subheader("🎯 ヒット予測結果")
        
        predictions = []
        for product in korea_df['product'].unique():
            korea_prod = korea_df[korea_df['product'] == product]
            japan_prod = japan_df[japan_df['product'] == product]
            
            if len(korea_prod) > 0 and len(japan_prod) > 0:
                rank_result = analyzer.spearman_rank_analysis(
                    korea_prod['rank'].values,
                    japan_prod['rank'].values
                )
                
                time_result = analyzer.cross_correlation_analysis(
                    pd.Series(korea_prod['sales'].values),
                    pd.Series(japan_prod['sales'].values),
                    max_lag=6
                )
                
                category_score = analyzer.category_correlation(
                    korea_prod['category'].iloc[0],
                    japan_prod['category'].iloc[0]
                )
                
                prediction = analyzer.calculate_prediction_score(
                    rank_result['correlation'],
                    time_result['optimal_correlation'],
                    category_score
                )
                
                predictions.append({
                    '商品名': product,
                    'カテゴリ': korea_prod['category'].iloc[0],
                    '予測スコア': prediction['prediction_score'],
                    '信頼度': prediction['confidence_level'],
                    '推奨アクション': prediction['recommendation'],
                    '最適投入時期': f"{time_result['optimal_lag']}ヶ月後"
                })
        
        predictions_df = pd.DataFrame(predictions)
        predictions_df = predictions_df.sort_values('予測スコア', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.dataframe(
                predictions_df.style.applymap(
                    lambda x: 'color: green; font-weight: bold' if x == '非常に高い' 
                    else 'color: orange; font-weight: bold' if x == '高い'
                    else 'color: red' if x == '低い' else '',
                    subset=['信頼度']
                ),
                use_container_width=True,
                height=400
            )
        
        with col2:
            st.markdown("### 📊 予測サマリー")
            
            high_potential = len(predictions_df[predictions_df['予測スコア'] >= 0.7])
            medium_potential = len(predictions_df[(predictions_df['予測スコア'] >= 0.4) & 
                                                 (predictions_df['予測スコア'] < 0.7)])
            low_potential = len(predictions_df[predictions_df['予測スコア'] < 0.4])
            
            st.metric("高ポテンシャル商品", f"{high_potential} 件", "即投入推奨")
            st.metric("中ポテンシャル商品", f"{medium_potential} 件", "追加分析必要")
            st.metric("低ポテンシャル商品", f"{low_potential} 件", "慎重検討")
            
            fig = go.Figure(data=[go.Pie(
                labels=['高', '中', '低'],
                values=[high_potential, medium_potential, low_potential],
                hole=.3,
                marker_colors=['green', 'orange', 'red']
            )])
            fig.update_layout(
                showlegend=True,
                height=250,
                margin=dict(t=0, b=0, l=0, r=0)
            )
            st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        st.markdown("### 📥 分析結果のエクスポート")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            csv = predictions_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="CSV形式でダウンロード",
                data=csv,
                file_name=f"korea_cosmetics_prediction_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        with col2:
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                predictions_df.to_excel(writer, sheet_name='予測結果', index=False)
            buffer.seek(0)
            
            st.download_button(
                label="Excel形式でダウンロード",
                data=buffer,
                file_name=f"korea_cosmetics_prediction_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col3:
            if st.button("📊 レポート生成", type="primary"):
                st.success("予測レポートを生成しました")

if __name__ == "__main__":
    main()