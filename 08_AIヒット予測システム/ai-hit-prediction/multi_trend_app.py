#!/usr/bin/env python
"""
Multi-Industry Trend Analysis Dashboard
複数業界対応トレンド分析ダッシュボード
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
from pathlib import Path
import sys
sys.path.append('.')

from src.analysis.multi_industry_trend import MultiIndustryTrendAnalyzer

# ページ設定
st.set_page_config(
    page_title="業界トレンド分析システム",
    page_icon="📊",
    layout="wide"
)

# セッション状態初期化
if 'selected_industries' not in st.session_state:
    st.session_state.selected_industries = []
if 'report_generated' not in st.session_state:
    st.session_state.report_generated = False
if 'current_report' not in st.session_state:
    st.session_state.current_report = None

def main():
    # ヘッダー
    st.title("📊 業界トレンド分析システム")
    st.caption("化粧品・インナービューティー・健康食品業界の統合分析")
    
    # 更新情報バー
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.info("📅 更新頻度: 週次")
    with col2:
        next_update = (datetime.now() + timedelta(days=(7 - datetime.now().weekday()))).strftime("%m/%d")
        st.info(f"🔄 次回更新: {next_update}")
    with col3:
        st.info("📊 データソース: 3種類")
    with col4:
        st.info("🎯 分析業界: 最大3業界")
    
    # サイドバー
    with st.sidebar:
        st.header("⚙️ 分析設定")
        
        # 業界選択
        st.subheader("📌 分析対象業界を選択")
        
        industries = {
            "cosmetics": {"name": "化粧品業界", "icon": "💄"},
            "inner_beauty": {"name": "インナービューティー・サプリ", "icon": "💊"},
            "health_food": {"name": "健康食品業界", "icon": "🥗"}
        }
        
        selected = []
        for key, info in industries.items():
            if st.checkbox(f"{info['icon']} {info['name']}", value=(key=="cosmetics")):
                selected.append(key)
        
        st.session_state.selected_industries = selected
        
        if len(selected) == 0:
            st.warning("少なくとも1つの業界を選択してください")
        
        st.divider()
        
        # 分析オプション
        st.subheader("🔧 分析オプション")
        
        include_academic = st.checkbox("学術研究トレンド", value=True)
        include_social = st.checkbox("ソーシャルトレンド", value=True) 
        include_market = st.checkbox("市場データ", value=True)
        include_cross = st.checkbox("業界横断分析", value=True, disabled=(len(selected)<2))
        
        st.divider()
        
        # レポート生成ボタン
        if st.button("📊 週次レポート生成", type="primary", disabled=(len(selected)==0)):
            st.session_state.report_generated = True
        
        # 自動更新設定
        st.divider()
        st.subheader("⏰ 自動更新設定")
        
        auto_update = st.checkbox("週次自動更新を有効化", value=True)
        if auto_update:
            update_day = st.selectbox(
                "更新曜日",
                ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日"],
                index=0
            )
            update_time = st.time_input("更新時刻", value=datetime.strptime("09:00", "%H:%M").time())
            st.success(f"毎週{update_day} {update_time}に自動更新")
    
    # メインコンテンツ
    if st.session_state.report_generated and st.session_state.selected_industries:
        generate_and_display_report()
    else:
        show_dashboard()

def show_dashboard():
    """ダッシュボード表示"""
    st.header("📈 トレンドダッシュボード")
    
    # 業界選択促進
    if not st.session_state.selected_industries:
        st.info("👈 左側のサイドバーから分析対象業界を選択してください")
        
        # 業界概要カード
        st.subheader("📋 分析可能な業界")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            with st.container():
                st.markdown("""
                ### 💄 化粧品業界
                - 市場規模: 2.8兆円
                - 成長率: +4.8%
                - 主要カテゴリ: スキンケア、メイク、ヘアケア
                - トレンド: クリーンビューティー、K-Beauty
                """)
        
        with col2:
            with st.container():
                st.markdown("""
                ### 💊 インナービューティー・サプリ
                - 市場規模: 8,500億円
                - 成長率: +7.5%
                - 主要カテゴリ: 美容サプリ、コラーゲン
                - トレンド: 腸活美容、プロテイン美容
                """)
        
        with col3:
            with st.container():
                st.markdown("""
                ### 🥗 健康食品業界
                - 市場規模: 1.3兆円
                - 成長率: +6.2%
                - 主要カテゴリ: 機能性表示食品、プロテイン
                - トレンド: 腸活、免疫サポート
                """)
    else:
        # 選択された業界の概要
        st.subheader("📌 選択中の業界")
        
        analyzer = MultiIndustryTrendAnalyzer()
        cols = st.columns(len(st.session_state.selected_industries))
        
        for i, industry in enumerate(st.session_state.selected_industries):
            info = analyzer.INDUSTRIES[industry]
            with cols[i]:
                st.metric(
                    f"{info['icon']} {info['name']}",
                    info["market_size"],
                    "分析対象"
                )
        
        # 前回のレポート情報
        st.divider()
        st.subheader("📅 レポート履歴")
        
        # ダミーデータ表示
        history_data = pd.DataFrame({
            "生成日": [
                (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"),
                (datetime.now() - timedelta(days=21)).strftime("%Y-%m-%d")
            ],
            "対象業界": ["化粧品", "化粧品、サプリ", "全業界"],
            "主要トレンド": ["ビタミンC", "腸活", "パーソナライズ"],
            "ステータス": ["完了", "完了", "完了"]
        })
        
        st.dataframe(history_data, use_container_width=True)

def generate_and_display_report():
    """レポート生成と表示"""
    
    # プログレスバー
    progress = st.progress(0)
    status = st.empty()
    
    # アナライザー初期化
    analyzer = MultiIndustryTrendAnalyzer()
    
    # レポート生成
    status.text("📊 週次レポートを生成中...")
    progress.progress(20)
    
    report = analyzer.generate_weekly_report(st.session_state.selected_industries)
    st.session_state.current_report = report
    
    progress.progress(100)
    status.text("✅ レポート生成完了！")
    
    # レポートヘッダー
    st.header("📊 週次業界トレンド分析レポート")
    st.caption(f"生成日時: {report['report_info']['generated_date'][:19]}")
    
    # タブ構成
    tabs = ["📈 サマリー", "📚 学術トレンド", "📱 ソーシャル", "🏢 市場データ"]
    if len(st.session_state.selected_industries) > 1:
        tabs.append("🔄 業界横断分析")
    tabs.append("💡 アクションプラン")
    
    tab_objects = st.tabs(tabs)
    
    # サマリータブ
    with tab_objects[0]:
        show_summary(report)
    
    # 学術トレンドタブ
    with tab_objects[1]:
        show_academic_trends_multi(report)
    
    # ソーシャルトレンドタブ
    with tab_objects[2]:
        show_social_trends_multi(report)
    
    # 市場データタブ
    with tab_objects[3]:
        show_market_data_multi(report)
    
    # 業界横断分析タブ（複数業界選択時）
    if len(st.session_state.selected_industries) > 1:
        with tab_objects[4]:
            show_cross_industry(report)
        action_tab_index = 5
    else:
        action_tab_index = 4
    
    # アクションプランタブ
    with tab_objects[action_tab_index]:
        show_action_plan(report)
    
    # エクスポート
    st.divider()
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.download_button(
            "📥 レポートをダウンロード (JSON)",
            data=json.dumps(report, indent=2, ensure_ascii=False),
            file_name=f"weekly_report_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )
    
    st.session_state.report_generated = False

def show_summary(report):
    """サマリー表示"""
    st.subheader("📊 エグゼクティブサマリー")
    
    # ハイライト表示
    for highlight in report["weekly_highlights"]:
        st.info(f"**{highlight['industry']}**: {highlight['highlight']}")
    
    # 各業界のサマリー
    for industry_key, data in report["industry_specific"].items():
        with st.expander(f"{data['icon']} {data['name']}", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("市場規模", data["market_data"]["market_size"])
                st.metric("成長率", data["market_data"]["growth_rate"])
            
            with col2:
                top_hashtag = data["social_trends"]["trending_hashtags"][0]
                st.metric("トップトレンド", top_hashtag["tag"])
                st.metric("成長率", top_hashtag["growth"])
            
            with col3:
                st.metric("新規参入", f"{data['market_data']['new_entries']}社")
                st.metric("M&A", f"{data['market_data']['ma_activities']}件")
            
            # 機会
            if data["opportunities"]:
                st.markdown("**🎯 ビジネス機会:**")
                for opp in data["opportunities"][:2]:
                    st.write(f"• {opp['opportunity']} ({opp['priority']}優先度)")

def show_academic_trends_multi(report):
    """学術トレンド表示（複数業界）"""
    st.subheader("📚 学術研究トレンド")
    
    for industry_key, data in report["industry_specific"].items():
        academic = data["academic_trends"]
        
        st.markdown(f"### {data['icon']} {data['name']}")
        
        # メトリクス
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("論文数", academic["total_papers"])
        with col2:
            st.metric("コラボ指数", f"{academic['collaboration_index']:.2f}")
        with col3:
            st.metric("分析期間", academic["period"])
        
        # 主要研究
        for research in academic["key_research"][:2]:
            with st.container():
                st.markdown(f"**{research['topic']}**")
                st.caption(f"論文数: {research['paper_count']} | 成長: {research['growth']}")
                st.info(research["key_finding"])
        
        st.divider()

def show_social_trends_multi(report):
    """ソーシャルトレンド表示（複数業界）"""
    st.subheader("📱 ソーシャルメディアトレンド")
    
    for industry_key, data in report["industry_specific"].items():
        social = data["social_trends"]
        
        st.markdown(f"### {data['icon']} {data['name']}")
        
        # トレンドハッシュタグ
        hashtag_df = pd.DataFrame(social["trending_hashtags"])
        st.dataframe(hashtag_df, use_container_width=True)
        
        # 消費者関心事
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**インフルエンサートピック:**")
            for topic in social["influencer_topics"]:
                st.write(f"• {topic}")
        
        with col2:
            st.markdown("**消費者の関心:**")
            for interest in social["consumer_interests"]:
                st.write(f"• {interest}")
        
        st.divider()

def show_market_data_multi(report):
    """市場データ表示（複数業界）"""
    st.subheader("🏢 市場データ分析")
    
    # 比較表
    comparison_data = []
    for industry_key, data in report["industry_specific"].items():
        market = data["market_data"]
        comparison_data.append({
            "業界": data["name"],
            "市場規模": market["market_size"],
            "成長率": market["growth_rate"],
            "新規参入": market["new_entries"],
            "M&A": market["ma_activities"]
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    st.dataframe(comparison_df, use_container_width=True)
    
    # 各業界の詳細
    for industry_key, data in report["industry_specific"].items():
        market = data["market_data"]
        
        with st.expander(f"{data['icon']} {data['name']}の詳細"):
            # セグメント分析
            st.markdown("**市場セグメント:**")
            segments_df = pd.DataFrame(market["segments"])
            st.bar_chart(segments_df.set_index("name")["share"])
            
            # 投資フォーカス
            st.markdown("**投資フォーカス分野:**")
            for focus in market["investment_focus"]:
                st.write(f"• {focus}")

def show_cross_industry(report):
    """業界横断分析表示"""
    st.subheader("🔄 業界横断分析")
    
    if report["cross_industry"]:
        cross = report["cross_industry"]
        
        # 共通トレンド
        st.markdown("### 🎯 業界共通トレンド")
        for trend in cross["common_trends"]:
            with st.expander(trend["trend"]):
                st.write(trend["description"])
                st.info(f"**ビジネス機会**: {trend['opportunity']}")
        
        # シナジー機会
        st.markdown("### 🤝 シナジー機会")
        for synergy in cross["synergy_opportunities"]:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.markdown(f"**{synergy['opportunity']}**")
                st.write(synergy["concept"])
                industries = ", ".join([MultiIndustryTrendAnalyzer.INDUSTRIES[i]["name"] 
                                       for i in synergy["industries"]])
                st.caption(f"対象: {industries}")
            with col2:
                st.metric("市場ポテンシャル", synergy["market_potential"])
        
        # テクノロジー収束
        st.markdown("### 🔬 テクノロジー収束")
        for tech in cross["technology_convergence"]:
            st.write(f"• {tech}")

def show_action_plan(report):
    """アクションプラン表示"""
    st.subheader("💡 週次アクションプラン")
    
    if report["action_items"]:
        for i, item in enumerate(report["action_items"], 1):
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{i}. {item['action']}**")
                    st.caption(f"対象: {item['industry']}")
                
                with col2:
                    priority_color = {"高": "🔴", "中": "🟡", "低": "🟢"}
                    st.write(f"{priority_color.get(item['priority'], '')} {item['priority']}優先度")
                
                with col3:
                    st.write(f"⏰ {item['timeline']}")
                
                with col4:
                    st.write(f"👥 {item['responsible']}")
                
                st.divider()
    
    # 次回更新
    st.info(f"📅 次回更新: {report['next_update_schedule']['date']} {report['next_update_schedule']['time']}")

if __name__ == "__main__":
    main()