#!/usr/bin/env python3
import json
import pandas as pd
import numpy as np
from datetime import datetime
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def load_data():
    with open('📊_論文データベース_2024年9月/📋_マスターデータ/統合データ（9,087件）', 'r') as f:
        data = json.load(f)
    return data

def extract_all_papers(data):
    all_papers = []
    for category, subcategories in data.items():
        if isinstance(subcategories, dict):
            for subcategory, papers_list in subcategories.items():
                if isinstance(papers_list, list):
                    for paper in papers_list:
                        paper_copy = paper.copy() if isinstance(paper, dict) else {'title': str(paper)}
                        paper_copy['main_category'] = category
                        paper_copy['sub_category'] = subcategory
                        all_papers.append(paper_copy)
    return all_papers

def analyze_papers(papers):
    df = pd.DataFrame(papers)

    print("\n" + "="*80)
    print("📊 論文データベース総合分析レポート")
    print("="*80)

    print(f"\n📚 総論文数: {len(df):,}件")

    print("\n📂 カテゴリ別論文数:")
    category_counts = df['main_category'].value_counts()
    for cat, count in category_counts.items():
        print(f"  • {cat}: {count:,}件 ({count/len(df)*100:.1f}%)")

    print("\n🔬 サブカテゴリ別TOP 20:")
    sub_counts = df['sub_category'].value_counts().head(20)
    for sub, count in sub_counts.items():
        print(f"  • {sub}: {count:,}件")

    if 'publication_date' in df.columns:
        df['year'] = pd.to_datetime(df['publication_date'], errors='coerce').dt.year
        valid_years = df['year'].dropna()
        if len(valid_years) > 0:
            print(f"\n📅 出版年の範囲: {int(valid_years.min())} - {int(valid_years.max())}")

            year_counts = valid_years.value_counts().sort_index()
            recent_years = year_counts[year_counts.index >= 2020]
            if len(recent_years) > 0:
                print("\n📈 近年の論文数推移 (2020年以降):")
                for year, count in recent_years.items():
                    print(f"  • {int(year)}年: {count:,}件")

    all_keywords = []
    for keywords_str in df['keywords'].dropna():
        if isinstance(keywords_str, str):
            keywords = [k.strip() for k in keywords_str.split(',') if k.strip()]
            all_keywords.extend(keywords)

    if all_keywords:
        keyword_counter = Counter(all_keywords)
        print(f"\n🔑 キーワード分析:")
        print(f"  • 総キーワード数: {len(keyword_counter):,}")
        print(f"  • 平均キーワード数/論文: {len(all_keywords)/len(df):.1f}")

        print("\n🏷️ TOP 30 頻出キーワード:")
        for keyword, count in keyword_counter.most_common(30):
            print(f"  • {keyword}: {count:,}回")

    trend_keywords = ['AI', 'machine learning', 'deep learning', 'personalized',
                     'microbiome', 'sustainability', 'natural', 'organic',
                     'collagen', 'peptide', 'CBD', 'probiotic', 'prebiotic']

    print("\n🔥 トレンドキーワード出現状況:")
    for trend in trend_keywords:
        count = sum(1 for k in all_keywords if trend.lower() in k.lower())
        if count > 0:
            print(f"  • {trend}: {count}件")

    return df

def create_visualizations(df):
    print("\n📊 可視化を生成中...")

    fig = plt.figure(figsize=(20, 12))

    ax1 = plt.subplot(2, 3, 1)
    category_counts = df['main_category'].value_counts()
    colors = plt.cm.Set3(np.linspace(0, 1, len(category_counts)))
    wedges, texts, autotexts = ax1.pie(category_counts.values,
                                        labels=category_counts.index,
                                        autopct='%1.1f%%',
                                        colors=colors,
                                        startangle=90)
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    ax1.set_title('メインカテゴリ別論文分布', fontsize=14, fontweight='bold')

    ax2 = plt.subplot(2, 3, 2)
    top_subs = df['sub_category'].value_counts().head(15)
    ax2.barh(range(len(top_subs)), top_subs.values, color='skyblue')
    ax2.set_yticks(range(len(top_subs)))
    ax2.set_yticklabels([s[:30] + '...' if len(s) > 30 else s for s in top_subs.index])
    ax2.set_xlabel('論文数')
    ax2.set_title('TOP 15 サブカテゴリ', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3)

    for i, v in enumerate(top_subs.values):
        ax2.text(v + 1, i, str(v), va='center')

    if 'year' in df.columns:
        ax3 = plt.subplot(2, 3, 3)
        year_counts = df['year'].value_counts().sort_index()
        recent_years = year_counts[year_counts.index >= 2015]
        if len(recent_years) > 0:
            ax3.plot(recent_years.index, recent_years.values, marker='o', linewidth=2, markersize=8)
            ax3.fill_between(recent_years.index, recent_years.values, alpha=0.3)
            ax3.set_xlabel('年')
            ax3.set_ylabel('論文数')
            ax3.set_title('年別論文数の推移 (2015年以降)', fontsize=14, fontweight='bold')
            ax3.grid(True, alpha=0.3)
            ax3.set_xticks(recent_years.index[::2])

    ax4 = plt.subplot(2, 3, 4)
    cat_sub_counts = df.groupby(['main_category', 'sub_category']).size()
    top_combinations = cat_sub_counts.nlargest(20)
    labels = [f"{idx[0][:15]}\n{idx[1][:20]}" for idx in top_combinations.index]
    bars = ax4.bar(range(len(top_combinations)), top_combinations.values, color='coral')
    ax4.set_xticks(range(len(top_combinations)))
    ax4.set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
    ax4.set_ylabel('論文数')
    ax4.set_title('カテゴリ×サブカテゴリ TOP 20', fontsize=14, fontweight='bold')
    ax4.grid(True, alpha=0.3)

    ax5 = plt.subplot(2, 3, 5)
    papers_per_sub = df.groupby('sub_category').size()
    ax5.hist(papers_per_sub.values, bins=30, color='lightgreen', edgecolor='darkgreen', alpha=0.7)
    ax5.set_xlabel('論文数')
    ax5.set_ylabel('サブカテゴリ数')
    ax5.set_title('サブカテゴリあたりの論文数分布', fontsize=14, fontweight='bold')
    ax5.grid(True, alpha=0.3)

    ax6 = plt.subplot(2, 3, 6)
    cat_diversity = df.groupby('main_category')['sub_category'].nunique().sort_values(ascending=False)
    ax6.bar(range(len(cat_diversity)), cat_diversity.values, color='mediumpurple')
    ax6.set_xticks(range(len(cat_diversity)))
    ax6.set_xticklabels(cat_diversity.index, rotation=45, ha='right')
    ax6.set_ylabel('サブカテゴリ数')
    ax6.set_title('カテゴリ別の多様性（サブカテゴリ数）', fontsize=14, fontweight='bold')
    ax6.grid(True, alpha=0.3)

    for i, v in enumerate(cat_diversity.values):
        ax6.text(i, v + 0.5, str(v), ha='center', fontweight='bold')

    plt.suptitle('論文データベース総合分析ダッシュボード', fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f'comprehensive_analysis_{timestamp}.png'
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"  ✅ 可視化を保存: {filename}")

    plt.show()

    return filename

def generate_insights(df):
    print("\n💡 インサイト生成:")

    insights = []

    top_category = df['main_category'].value_counts().index[0]
    top_category_pct = df['main_category'].value_counts().values[0] / len(df) * 100
    insights.append(f"最も研究が活発な分野は「{top_category}」で、全体の{top_category_pct:.1f}%を占める")

    top_sub = df['sub_category'].value_counts().index[0]
    top_sub_count = df['sub_category'].value_counts().values[0]
    insights.append(f"最も論文数が多いサブカテゴリは「{top_sub}」（{top_sub_count}件）")

    if 'year' in df.columns:
        recent_papers = df[df['year'] >= 2023]
        if len(recent_papers) > 0:
            recent_top_cat = recent_papers['main_category'].value_counts().index[0]
            insights.append(f"2023年以降の最新研究は「{recent_top_cat}」分野に集中")

    cat_diversity = df.groupby('main_category')['sub_category'].nunique()
    most_diverse = cat_diversity.idxmax()
    insights.append(f"最も多様な研究領域は「{most_diverse}」（{cat_diversity[most_diverse]}のサブカテゴリ）")

    papers_per_sub = df.groupby('sub_category').size()
    concentrated_subs = papers_per_sub[papers_per_sub >= 100]
    if len(concentrated_subs) > 0:
        insights.append(f"100件以上の論文が集中している領域が{len(concentrated_subs)}個存在")

    for i, insight in enumerate(insights, 1):
        print(f"  {i}. {insight}")

    return insights

def main():
    print("\n🚀 総合データ分析を開始します...")

    data = load_data()
    papers = extract_all_papers(data)

    df = analyze_papers(papers)

    visualization_file = create_visualizations(df)

    insights = generate_insights(df)

    report = {
        'analysis_date': datetime.now().isoformat(),
        'total_papers': len(df),
        'categories': df['main_category'].value_counts().to_dict(),
        'top_subcategories': df['sub_category'].value_counts().head(20).to_dict(),
        'insights': insights,
        'visualization': visualization_file
    }

    report_file = f'analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 分析レポートを保存: {report_file}")
    print("\n🎉 分析が完了しました！")

if __name__ == "__main__":
    main()