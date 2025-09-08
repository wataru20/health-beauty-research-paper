#!/usr/bin/env python
"""
Trend Analysis Dashboard
トレンド分析ダッシュボード - Streamlit App
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
sys.path.append('.')

# トレンド分析モジュールのインポート
from src.analysis.trend_report import TrendAnalyzer

# ページ設定
st.set_page_config(
    page_title="トレンド分析ダッシュボード",
    page_icon="📊",
    layout="wide"
)

# カスタムCSS
st.markdown("""
<style>
    .trend-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 8px;
        margin: 5px 0;
    }
    .insight-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # ヘッダー
    st.title("📊 トレンド分析ダッシュボード")
    st.subheader("化粧品業界の統合トレンド分析レポート")
    
    # サイドバー
    with st.sidebar:
        st.header("⚙️ 分析設定")
        
        # 分析期間選択
        period = st.selectbox(
            "分析期間",
            ["過去1ヶ月", "過去3ヶ月", "過去6ヶ月", "過去1年"]
        )
        
        # データソース選択
        st.subheader("データソース")
        use_academic = st.checkbox("学術研究データ", value=True)
        use_social = st.checkbox("ソーシャルメディア", value=True)
        use_industry = st.checkbox("業界データ", value=True)
        
        # 分析実行ボタン
        if st.button("🔄 最新データで分析実行", type="primary"):
            st.session_state.analyzing = True
        
        st.divider()
        
        # レポート情報
        st.info("""
        **データソース情報**
        - 📚 学術: Semantic Scholar
        - 📱 SNS: Instagram, TikTok, X
        - 🏢 業界: プレスリリース、市場レポート
        
        **更新頻度**
        - リアルタイム〜日次更新
        """)
    
    # メインコンテンツ
    if 'analyzing' not in st.session_state:
        st.session_state.analyzing = False
    
    if st.session_state.analyzing or st.button("📊 トレンド分析を開始"):
        analyze_trends()
    else:
        show_welcome()

def show_welcome():
    """ウェルカム画面表示"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="trend-card">
        <h3>📚 学術研究トレンド</h3>
        <p>最新の研究論文から<br>革新的な成分や技術を発見</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="trend-card">
        <h3>📱 ソーシャルトレンド</h3>
        <p>SNSやインフルエンサーから<br>消費者ニーズを把握</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="trend-card">
        <h3>🏢 業界トレンド</h3>
        <p>企業動向や市場データから<br>ビジネス機会を特定</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🎯 このダッシュボードでできること")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        - ✅ 3つのデータソースからトレンドを自動収集
        - ✅ AIによる統合分析とパターン検出
        - ✅ ビジネス機会の特定と優先順位付け
        """)
    
    with col2:
        st.markdown("""
        - ✅ 戦略的インサイトの生成
        - ✅ アクションプランの提案
        - ✅ レポートのエクスポート機能
        """)

def analyze_trends():
    """トレンド分析実行"""
    st.session_state.analyzing = False
    
    # プログレスバー
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # 分析実行
    analyzer = TrendAnalyzer()
    
    status_text.text("📚 学術研究データを収集中...")
    progress_bar.progress(25)
    academic = analyzer.collect_academic_trends()
    
    status_text.text("📱 ソーシャルメディアデータを収集中...")
    progress_bar.progress(50)
    social = analyzer.collect_social_trends()
    
    status_text.text("🏢 業界データを収集中...")
    progress_bar.progress(75)
    industry = analyzer.collect_industry_trends()
    
    status_text.text("🔄 統合分析を実行中...")
    progress_bar.progress(90)
    convergence = analyzer.analyze_convergence(academic, social, industry)
    insights = analyzer.generate_strategic_insights(convergence)
    
    progress_bar.progress(100)
    status_text.text("✅ 分析完了！")
    
    # タブ表示
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 統合分析", "📚 学術トレンド", "📱 ソーシャル", 
        "🏢 業界動向", "💡 戦略提案"
    ])
    
    with tab1:
        show_integrated_analysis(convergence, insights)
    
    with tab2:
        show_academic_trends(academic)
    
    with tab3:
        show_social_trends(social)
    
    with tab4:
        show_industry_trends(industry)
    
    with tab5:
        show_strategic_recommendations(insights)
    
    # エクスポート機能
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col2:
        report = {
            "academic": academic,
            "social": social,
            "industry": industry,
            "convergence": convergence,
            "insights": insights,
            "generated_at": datetime.now().isoformat()
        }
        
        st.download_button(
            label="📥 レポートをダウンロード (JSON)",
            data=json.dumps(report, indent=2, ensure_ascii=False),
            file_name=f"trend_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

def show_integrated_analysis(convergence, insights):
    """統合分析の表示"""
    st.header("🔄 統合トレンド分析")
    
    # トレンド収束スコア
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            "トレンド収束度",
            f"{convergence['trend_alignment_score']*100:.0f}%",
            delta="+5%"
        )
    with col2:
        st.metric(
            "市場機会",
            "1,300億円",
            delta="+15%"
        )
    with col3:
        st.metric(
            "成功確率",
            "82%",
            delta="+3%"
        )
    
    # 主要パターン
    st.subheader("🎯 検出された主要トレンドパターン")
    
    for pattern in convergence["cross_trend_patterns"]:
        with st.expander(f"📍 {pattern['pattern']}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("**エビデンス:**")
                for source, evidence in pattern["evidence"].items():
                    st.write(f"• {source}: {evidence}")
                
                st.markdown(f"**推奨アクション:** {pattern['recommendation']}")
            
            with col2:
                opportunity_score = pattern["opportunity_score"] * 100
                st.metric("機会スコア", f"{opportunity_score:.0f}%")
                
                # スコアに応じた色分け
                if opportunity_score >= 80:
                    st.success("高ポテンシャル")
                elif opportunity_score >= 60:
                    st.warning("中ポテンシャル")
                else:
                    st.info("要検討")
    
    # 市場準備度
    st.subheader("⏰ 市場投入タイミング")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**即時投入可能**")
        for item in convergence["market_readiness"]["immediate"]:
            st.write(f"• {item}")
    
    with col2:
        st.markdown("**短期（3-6ヶ月）**")
        for item in convergence["market_readiness"]["short_term"]:
            st.write(f"• {item}")
    
    with col3:
        st.markdown("**長期（6ヶ月以上）**")
        for item in convergence["market_readiness"]["long_term"]:
            st.write(f"• {item}")

def show_academic_trends(academic):
    """学術トレンドの表示"""
    st.header("📚 学術研究トレンド分析")
    
    # メトリクス
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("分析論文数", f"{academic['total_papers']:,}")
    with col2:
        st.metric("注目成分", "3種")
    with col3:
        st.metric("研究成長率", "+45%")
    with col4:
        st.metric("期間", academic["period"])
    
    # 主要発見
    st.subheader("🔬 主要研究トピック")
    
    for finding in academic["key_findings"]:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.markdown(f"**{finding['topic']}**")
                st.caption(finding['key_insight'])
            with col2:
                st.metric("論文数", finding['paper_count'])
            with col3:
                if finding['trend'] == "急上昇":
                    st.success(f"📈 {finding['trend']}")
                elif finding['trend'] == "上昇":
                    st.warning(f"📈 {finding['trend']}")
                else:
                    st.info(f"➡️ {finding['trend']}")
    
    # 新興成分
    st.subheader("🧪 注目の新成分")
    
    ingredients_df = pd.DataFrame(academic["emerging_ingredients"])
    st.bar_chart(ingredients_df.set_index("name")["growth_rate"])

def show_social_trends(social):
    """ソーシャルトレンドの表示"""
    st.header("📱 ソーシャルメディアトレンド")
    
    # メトリクス
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("総メンション", f"{social['total_mentions']:,}")
    with col2:
        st.metric("分析プラットフォーム", len(social['platforms_analyzed']))
    with col3:
        st.metric("トレンドタグ", len(social['trending_hashtags']))
    with col4:
        st.metric("期間", social["period"])
    
    # トレンディングハッシュタグ
    st.subheader("🔥 トレンディングハッシュタグ")
    
    for tag in social["trending_hashtags"]:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col1:
            st.markdown(f"**{tag['tag']}**")
            st.caption(tag['description'])
        with col2:
            st.metric("メンション", f"{tag['mentions']:,}")
        with col3:
            st.metric("成長率", tag['growth'])
        with col4:
            sentiment = tag['sentiment'] * 100
            st.metric("好感度", f"{sentiment:.0f}%")
    
    # 消費者の関心事
    st.subheader("💭 消費者の関心事")
    
    concerns_df = pd.DataFrame(social["consumer_concerns"])
    st.bar_chart(concerns_df.set_index("concern")["frequency"])

def show_industry_trends(industry):
    """業界トレンドの表示"""
    st.header("🏢 業界動向分析")
    
    # メトリクス
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("市場規模", industry['market_size'])
    with col2:
        st.metric("成長率", industry['growth_rate'])
    with col3:
        st.metric("新製品", len(industry['major_launches']))
    with col4:
        st.metric("期間", industry["period"])
    
    # 市場セグメント
    st.subheader("📊 市場セグメント別シェア")
    
    segments_data = []
    for segment, data in industry["market_segments"].items():
        segments_data.append({
            "セグメント": segment,
            "シェア(%)": data["share"],
            "成長率": data["growth"]
        })
    
    segments_df = pd.DataFrame(segments_data)
    
    col1, col2 = st.columns(2)
    with col1:
        st.bar_chart(segments_df.set_index("セグメント")["シェア(%)"])
    
    with col2:
        # 投資トレンド
        st.subheader("💰 投資トレンド")
        for invest in industry["investment_trends"]:
            st.write(f"**{invest['category']}**")
            st.write(f"投資額: {invest['investment']} ({invest['growth']})")

def show_strategic_recommendations(insights):
    """戦略的推奨事項の表示"""
    st.header("💡 戦略的推奨事項")
    
    # トップ機会
    st.subheader("🎯 最優先ビジネス機会")
    
    for i, opp in enumerate(insights["top_opportunities"], 1):
        with st.expander(f"機会 {i}: {opp['opportunity']}", expanded=(i==1)):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown(f"**根拠:** {opp['rationale']}")
                st.markdown(f"**ターゲット:** {opp['target_segment']}")
                st.markdown("**成功要因:**")
                for factor in opp['key_success_factors']:
                    st.write(f"• {factor}")
            
            with col2:
                st.metric("市場規模", opp['estimated_market_size'])
                success_prob = opp['success_probability'] * 100
                st.metric("成功確率", f"{success_prob:.0f}%")
                
                if success_prob >= 80:
                    st.success("推奨度: 高")
                elif success_prob >= 60:
                    st.warning("推奨度: 中")
                else:
                    st.info("推奨度: 要検討")
    
    # タイミング推奨
    st.subheader("📅 実行タイムライン")
    
    timeline = insights["timing_recommendations"]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**🚀 即時実行**")
        for action in timeline["immediate_action"]:
            st.checkbox(action, key=f"immediate_{action}")
    
    with col2:
        st.markdown("**📅 3ヶ月計画**")
        for action in timeline["3_month_plan"]:
            st.checkbox(action, key=f"3month_{action}")
    
    with col3:
        st.markdown("**📆 6ヶ月計画**")
        for action in timeline["6_month_plan"]:
            st.checkbox(action, key=f"6month_{action}")
    
    # リスク要因
    st.subheader("⚠️ リスク要因と対策")
    
    for risk in insights["risk_factors"]:
        col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
        with col1:
            st.write(f"**{risk['risk']}**")
        with col2:
            prob = risk['probability'] * 100
            st.write(f"確率: {prob:.0f}%")
        with col3:
            impact_color = {"高": "🔴", "中": "🟡", "低": "🟢"}
            st.write(f"影響: {impact_color.get(risk['impact'], '')} {risk['impact']}")
        with col4:
            st.caption(f"対策: {risk['mitigation']}")

if __name__ == "__main__":
    main()