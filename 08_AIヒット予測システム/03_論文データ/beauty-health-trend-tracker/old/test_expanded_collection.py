#!/usr/bin/env python3
"""
拡張キーワード収集のテストスクリプト
少数のキーワードで実際の収集をテストして、データ量と品質を確認
"""

import sys
import os
sys.path.append(os.getcwd())
from src.expanded_keywords_collection import ExpandedDataCollection
import json
from datetime import datetime

def run_test_collection():
    """テスト収集を実行"""
    print("""
    ====================================
    拡張キーワード収集テスト
    ====================================

    各カテゴリから2キーワードずつ選んでテスト収集します。
    """)

    collector = ExpandedDataCollection()

    # テスト用キーワード（各カテゴリから2つずつ）
    test_keywords = {
        "beauty_aging": ["skin elasticity", "anti-aging"],
        "health_wellness": ["gut health", "immune boost"],
        "mental_physical_performance": ["stress relief", "sleep quality"],
        "diet_body_contouring": ["weight loss", "intermittent fasting"],
        "trending_ingredients": ["collagen supplement", "NMN nicotinamide mononucleotide"],
        "emerging_ingredients": ["CBD cannabidiol", "exosome"]
    }

    test_results = {
        'test_date': datetime.now().isoformat(),
        'categories': {},
        'total_papers': 0,
        'total_keywords': 0,
        'average_papers_per_keyword': 0
    }

    print("テスト収集開始...\n")

    for category, keywords in test_keywords.items():
        print(f"\n■ カテゴリー: {category}")
        category_results = []

        for keyword in keywords:
            print(f"  収集中: {keyword}...", end='')

            try:
                papers = collector.collect_papers_for_keyword(
                    keyword=keyword,
                    max_results=30,  # テスト用に少なめ
                    years=2  # 直近2年分
                )

                result = {
                    'keyword': keyword,
                    'papers_count': len(papers),
                    'sample_titles': [p.get('title', '')[:100] for p in papers[:3]] if papers else []
                }

                category_results.append(result)
                test_results['total_papers'] += len(papers)
                test_results['total_keywords'] += 1

                print(f" {len(papers)}件")

                # サンプルタイトル表示
                if papers and len(papers) > 0:
                    print(f"    サンプル: {papers[0].get('title', 'タイトルなし')[:80]}...")

            except Exception as e:
                print(f" エラー: {e}")
                category_results.append({
                    'keyword': keyword,
                    'error': str(e)
                })

        test_results['categories'][category] = category_results

    # 平均論文数を計算
    if test_results['total_keywords'] > 0:
        test_results['average_papers_per_keyword'] = (
            test_results['total_papers'] / test_results['total_keywords']
        )

    # 結果を保存
    test_file = 'test_expanded_collection_results.json'
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, ensure_ascii=False, indent=2)

    # サマリー表示
    print(f"""
    ====================================
    テスト結果サマリー
    ====================================

    テストキーワード数: {test_results['total_keywords']}
    収集論文総数: {test_results['total_papers']}
    1キーワードあたり平均: {test_results['average_papers_per_keyword']:.1f}件

    結果ファイル: {test_file}
    """)

    # 全体推定
    total_keywords = len(collector.get_all_keywords())
    estimated_total = int(test_results['average_papers_per_keyword'] * total_keywords)

    print(f"""
    ====================================
    全キーワード収集時の推定
    ====================================

    全キーワード数: {total_keywords}
    推定総論文数: {estimated_total:,}件
    推定所要時間: {(total_keywords * 0.5) / 60:.1f}分

    現在のデータ（4,251件）と比較:
    約{estimated_total / 4251:.1f}倍のデータ量
    """)

    return test_results

def analyze_test_results(results):
    """テスト結果を分析"""
    print("""
    ====================================
    詳細分析
    ====================================
    """)

    # カテゴリー別の論文数
    print("\nカテゴリー別収集数:")
    for category, keywords_results in results['categories'].items():
        total = sum(kr.get('papers_count', 0) for kr in keywords_results)
        print(f"  - {category}: {total}件")

    # 最も論文数が多いキーワード
    all_keywords = []
    for keywords_results in results['categories'].values():
        all_keywords.extend(keywords_results)

    sorted_keywords = sorted(
        [k for k in all_keywords if 'papers_count' in k],
        key=lambda x: x['papers_count'],
        reverse=True
    )

    if sorted_keywords:
        print("\n論文数TOP3キーワード:")
        for i, kw in enumerate(sorted_keywords[:3], 1):
            print(f"  {i}. {kw['keyword']}: {kw['papers_count']}件")

if __name__ == "__main__":
    results = run_test_collection()
    analyze_test_results(results)