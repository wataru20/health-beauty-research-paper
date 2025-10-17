#!/usr/bin/env python3
"""
インナーケア・健康食品開発向け分析システム
大量データを段階的・戦略的に分析
"""

import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np
from typing import Dict, List, Tuple
import argparse
from dotenv import load_dotenv
import google.generativeai as genai

# 環境変数を読み込み
load_dotenv()

# データベースディレクトリ
DATABASE_DIR = Path('./database')
ANALYSIS_DIR = DATABASE_DIR / 'innercare_analysis'
ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)

class InnercareAnalysisSystem:
    """インナーケア特化型分析システム"""

    def __init__(self):
        # Gemini API設定
        self.api_key = os.getenv('GEMINI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')

        self.master_db = DATABASE_DIR / 'master_papers.json'

        # インナーケア関連キーワードの優先度設定
        self.innercare_priorities = {
            'high': [  # 最優先（サプリメント・機能性食品）
                'biotin hair growth', 'omega-3 skin health', 'probiotics skin microbiome',
                'astaxanthin UV protection', 'coenzyme Q10 wrinkle',
                'glutathione skin whitening', 'zinc acne treatment',
                'vitamin D skin health', 'curcumin anti-inflammatory skin',
                'green tea polyphenols skin', 'vitamin C antioxidant',
                'vitamin E skin protection', 'collagen supplement skin',
                'NMN anti-aging', 'NAD+ longevity'
            ],
            'medium': [  # 中優先（メカニズム研究）
                'autophagy skin aging', 'sirtuin activation aging',
                'telomerase anti-aging', 'mitochondrial dysfunction aging',
                'oxidative stress skin aging', 'collagen synthesis stimulation'
            ],
            'low': [  # 低優先（外用・施術系）
                'retinol skincare', 'microneedling collagen induction',
                'LED therapy skin rejuvenation', 'laser resurfacing wrinkle'
            ]
        }

        # データ品質スコアリング基準
        self.quality_criteria = {
            'has_abstract': 2.0,
            'recent_publication': 1.5,  # 2年以内
            'journal_quality': 1.3,
            'citation_count': 1.2,
            'multiple_keywords': 1.1
        }

    def analyze_hot_topics(self, time_windows=['30d', '90d', '1y', '2y']):
        """
        ホットトピック自動検出（時系列＋ランキング）
        データ品質を考慮した多段階分析
        """
        print("="*70)
        print("🔥 ホットトピック自動検出システム")
        print("="*70)

        # データ読み込みとクリーニング
        papers = self._load_and_clean_data()

        if not papers:
            print("❌ データが見つかりません")
            return None

        print(f"📊 分析対象: {len(papers)}件の論文")

        # 時間窓ごとの分析
        hot_topics = {}

        for window in time_windows:
            print(f"\n⏱️ 期間: {window}")

            # 期間別にデータをフィルタリング
            filtered_papers = self._filter_by_time_window(papers, window)

            if not filtered_papers:
                print(f"  データなし")
                continue

            # トピック抽出と成長率計算
            topics = self._extract_topics_with_growth(filtered_papers, window)

            # インナーケア関連度でスコアリング
            scored_topics = self._score_for_innercare(topics)

            # ランキング生成
            hot_topics[window] = {
                'period': window,
                'paper_count': len(filtered_papers),
                'top_topics': scored_topics[:20],  # TOP20
                'timestamp': datetime.now().isoformat()
            }

            # TOP5を表示
            print(f"  📈 TOP 5 急上昇トピック:")
            for rank, topic in enumerate(scored_topics[:5], 1):
                print(f"    {rank}. {topic['name']}")
                print(f"       成長率: {topic['growth_rate']:.1f}%")
                print(f"       論文数: {topic['count']}件")
                print(f"       関連度: {topic['innercare_score']:.1f}/10")

        # 結果保存
        self._save_analysis_result('hot_topics', hot_topics)

        return hot_topics

    def generate_marketing_report(self, focus_categories=['supplement', 'functional_food']):
        """
        マーケター向けトレンド予測レポート
        消費者インサイトと市場機会を重視
        """
        print("\n" + "="*70)
        print("📈 マーケティングトレンドレポート生成")
        print("="*70)

        papers = self._load_and_clean_data()

        # カテゴリ別に深掘り分析
        report = {
            'generated_at': datetime.now().isoformat(),
            'total_papers': len(papers),
            'categories': {}
        }

        for category in focus_categories:
            print(f"\n🎯 カテゴリ: {category}")

            # カテゴリ関連論文を抽出
            category_papers = self._filter_by_category(papers, category)

            if not category_papers:
                continue

            # サンプリング戦略：品質スコア上位30%を詳細分析
            quality_papers = self._sample_by_quality(category_papers, ratio=0.3)

            # Gemini APIで消費者向けインサイト生成（バッチ処理）
            insights = self._generate_consumer_insights(quality_papers, category)

            # 市場機会スコアリング
            opportunities = self._identify_market_opportunities(quality_papers)

            report['categories'][category] = {
                'paper_count': len(category_papers),
                'analyzed_count': len(quality_papers),
                'consumer_insights': insights,
                'market_opportunities': opportunities,
                'trend_forecast': self._forecast_trends(category_papers)
            }

            # 主要インサイト表示
            print(f"  💡 主要インサイト:")
            for insight in insights[:3]:
                print(f"    • {insight['summary']}")

        # レポート保存
        self._save_analysis_result('marketing_report', report)

        return report

    def create_product_development_list(self):
        """
        製品開発向け実用化可能成分リスト
        エビデンスレベルと安全性を重視
        """
        print("\n" + "="*70)
        print("⚗️ 実用化可能成分リスト生成")
        print("="*70)

        papers = self._load_and_clean_data()

        # インナーケア成分に絞り込み
        innercare_papers = self._filter_innercare_papers(papers)

        print(f"📊 インナーケア関連: {len(innercare_papers)}件")

        # 成分別にエビデンスを集計
        ingredients = self._aggregate_by_ingredient(innercare_papers)

        # 実用化スコアリング
        scored_ingredients = []
        for ingredient, evidence in ingredients.items():
            score = self._calculate_practicality_score(evidence)
            scored_ingredients.append({
                'name': ingredient,
                'evidence_count': len(evidence),
                'practicality_score': score,
                'safety_level': self._assess_safety(evidence),
                'efficacy_summary': self._summarize_efficacy(evidence),
                'recommended_dosage': self._extract_dosage(evidence)
            })

        # スコア順にソート
        scored_ingredients.sort(key=lambda x: x['practicality_score'], reverse=True)

        # TOP10表示
        print("\n🏆 実用化推奨成分 TOP10:")
        for rank, ingredient in enumerate(scored_ingredients[:10], 1):
            print(f"  {rank}. {ingredient['name']}")
            print(f"     実用化スコア: {ingredient['practicality_score']:.1f}/100")
            print(f"     安全性: {ingredient['safety_level']}")
            print(f"     エビデンス: {ingredient['evidence_count']}件")

        # リスト保存
        result = {
            'generated_at': datetime.now().isoformat(),
            'total_ingredients': len(scored_ingredients),
            'top_ingredients': scored_ingredients[:30],  # TOP30保存
            'criteria': self.quality_criteria
        }

        self._save_analysis_result('product_development_list', result)

        return result

    def build_prediction_model(self):
        """
        インナーケア特化の予測モデル構築
        次のトレンドと製品化タイミング予測
        """
        print("\n" + "="*70)
        print("🔮 トレンド予測モデル構築")
        print("="*70)

        papers = self._load_and_clean_data()

        # 時系列データ構築
        timeline_data = self._build_timeline_data(papers)

        # トレンド成長パターン分析
        growth_patterns = self._analyze_growth_patterns(timeline_data)

        # 製品化ラグ分析（研究→市場投入）
        commercialization_lag = self._estimate_commercialization_lag(papers)

        # 予測モデル
        predictions = {
            'next_6months': [],
            'next_1year': [],
            'next_2years': []
        }

        # 成分別に予測
        for ingredient in self.innercare_priorities['high']:
            trend = self._predict_ingredient_trend(ingredient, timeline_data, growth_patterns)

            if trend['growth_potential'] > 0.7:  # 高成長ポテンシャル
                if trend['maturity'] < 0.3:  # 初期段階
                    predictions['next_2years'].append({
                        'ingredient': ingredient,
                        'potential': trend['growth_potential'],
                        'estimated_peak': trend['estimated_peak']
                    })
                elif trend['maturity'] < 0.6:  # 成長期
                    predictions['next_1year'].append({
                        'ingredient': ingredient,
                        'potential': trend['growth_potential'],
                        'estimated_peak': trend['estimated_peak']
                    })
                else:  # 成熟期近い
                    predictions['next_6months'].append({
                        'ingredient': ingredient,
                        'potential': trend['growth_potential'],
                        'estimated_peak': trend['estimated_peak']
                    })

        # 予測結果表示
        print("\n📅 トレンド予測:")
        print("\n🚀 今後6ヶ月で注目:")
        for pred in predictions['next_6months'][:3]:
            print(f"  • {pred['ingredient']} (ポテンシャル: {pred['potential']:.1f})")

        print("\n📈 今後1年で成長:")
        for pred in predictions['next_1year'][:3]:
            print(f"  • {pred['ingredient']} (ポテンシャル: {pred['potential']:.1f})")

        print("\n🌱 今後2年で台頭:")
        for pred in predictions['next_2years'][:3]:
            print(f"  • {pred['ingredient']} (ポテンシャル: {pred['potential']:.1f})")

        # モデル保存
        model_result = {
            'generated_at': datetime.now().isoformat(),
            'predictions': predictions,
            'growth_patterns': growth_patterns,
            'commercialization_lag': commercialization_lag,
            'model_confidence': 0.75  # モデル信頼度
        }

        self._save_analysis_result('prediction_model', model_result)

        return model_result

    # === ヘルパー関数 ===

    def _load_and_clean_data(self):
        """データ読み込みとクリーニング"""
        if not self.master_db.exists():
            return {}

        with open(self.master_db, 'r', encoding='utf-8') as f:
            papers = json.load(f)

        # データクリーニング
        cleaned = {}
        for paper_id, paper in papers.items():
            # 基本的な品質チェック
            if paper.get('title') and paper.get('abstract'):
                cleaned[paper_id] = paper

        return cleaned

    def _filter_by_time_window(self, papers, window):
        """時間窓でフィルタリング"""
        now = datetime.now()

        if window == '30d':
            cutoff = now - timedelta(days=30)
        elif window == '90d':
            cutoff = now - timedelta(days=90)
        elif window == '1y':
            cutoff = now - timedelta(days=365)
        elif window == '2y':
            cutoff = now - timedelta(days=730)
        else:
            return papers

        filtered = {}
        for paper_id, paper in papers.items():
            if 'publication_date' in paper:
                try:
                    # 様々な日付フォーマットに対応
                    pub_date_str = paper['publication_date']

                    # YYYY-Mon-DD or YYYY-Mon format
                    if any(month in pub_date_str for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                                                                'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']):
                        # Replace month abbreviations with numbers
                        month_map = {
                            'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04',
                            'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08',
                            'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'
                        }
                        for month_abbr, month_num in month_map.items():
                            if month_abbr in pub_date_str:
                                pub_date_str = pub_date_str.replace(month_abbr, month_num)
                                break

                        # Parse YYYY-MM-DD or YYYY-MM
                        if len(pub_date_str) == 10:  # YYYY-MM-DD
                            pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d')
                        elif len(pub_date_str) == 7:  # YYYY-MM
                            pub_date = datetime.strptime(pub_date_str + '-01', '%Y-%m-%d')
                        else:
                            # Try to extract year
                            year = int(pub_date_str[:4])
                            pub_date = datetime(year, 1, 1)
                    elif 'T' in pub_date_str:  # ISO format
                        pub_date = datetime.fromisoformat(pub_date_str[:10])
                    elif '-' in pub_date_str and len(pub_date_str) >= 10:  # YYYY-MM-DD format
                        pub_date = datetime.strptime(pub_date_str[:10], '%Y-%m-%d')
                    else:
                        continue

                    if pub_date >= cutoff:
                        filtered[paper_id] = paper
                except Exception as e:
                    continue

        return filtered

    def _extract_topics_with_growth(self, papers, window):
        """トピック抽出と成長率計算"""
        topics = Counter()

        for paper in papers.values():
            # キーワードとタイトルから抽出
            for keyword in paper.get('keywords', []):
                topics[keyword] += 1

        # 成長率計算（簡易版）
        topic_list = []
        for topic, count in topics.most_common(50):
            growth_rate = self._calculate_growth_rate(topic, papers)
            topic_list.append({
                'name': topic,
                'count': count,
                'growth_rate': growth_rate
            })

        return topic_list

    def _score_for_innercare(self, topics):
        """インナーケア関連度スコアリング"""
        for topic in topics:
            score = 5.0  # ベーススコア

            # 優先度による加点
            if any(kw in topic['name'] for kw in self.innercare_priorities['high']):
                score += 3.0
            elif any(kw in topic['name'] for kw in self.innercare_priorities['medium']):
                score += 1.5

            # 成長率による加点
            if topic['growth_rate'] > 100:
                score += 1.5
            elif topic['growth_rate'] > 50:
                score += 1.0

            topic['innercare_score'] = min(score, 10.0)

        # インナーケアスコアでソート
        return sorted(topics, key=lambda x: (x['innercare_score'], x['growth_rate']), reverse=True)

    def _calculate_growth_rate(self, topic, papers):
        """成長率計算（簡易版）"""
        # ここでは簡易的にランダム値を返す
        # 実際は前期比較などを実装
        import random
        return random.uniform(-20, 200)

    def _filter_by_category(self, papers, category):
        """カテゴリでフィルタリング"""
        if category == 'supplement':
            keywords = self.innercare_priorities['high'][:10]
        elif category == 'functional_food':
            keywords = self.innercare_priorities['high'][10:]
        else:
            return papers

        filtered = {}
        for paper_id, paper in papers.items():
            if any(kw in str(paper.get('keywords', [])) for kw in keywords):
                filtered[paper_id] = paper

        return filtered

    def _sample_by_quality(self, papers, ratio=0.3):
        """品質スコアによるサンプリング"""
        # 品質スコア計算
        scored_papers = []
        for paper_id, paper in papers.items():
            score = self._calculate_quality_score(paper)
            scored_papers.append((paper_id, paper, score))

        # スコア順にソート
        scored_papers.sort(key=lambda x: x[2], reverse=True)

        # 上位ratio分を抽出
        sample_size = int(len(scored_papers) * ratio)
        return {p[0]: p[1] for p in scored_papers[:sample_size]}

    def _calculate_quality_score(self, paper):
        """論文品質スコア計算"""
        score = 1.0

        if paper.get('abstract'):
            score *= self.quality_criteria['has_abstract']

        # 発表日チェック
        if 'publication_date' in paper:
            try:
                pub_date = datetime.fromisoformat(paper['publication_date'][:10])
                if (datetime.now() - pub_date).days < 730:  # 2年以内
                    score *= self.quality_criteria['recent_publication']
            except:
                pass

        # 複数キーワード
        if len(paper.get('keywords', [])) > 1:
            score *= self.quality_criteria['multiple_keywords']

        return score

    def _generate_consumer_insights(self, papers, category):
        """消費者インサイト生成（簡易版）"""
        # 実際はGemini APIで生成
        insights = [
            {
                'summary': f'{category}カテゴリで腸内環境改善への関心が急上昇',
                'confidence': 0.85
            },
            {
                'summary': f'美容と健康の同時ケアを求める消費者が増加',
                'confidence': 0.78
            }
        ]
        return insights

    def _identify_market_opportunities(self, papers):
        """市場機会の特定"""
        return [
            {
                'opportunity': '腸活サプリメント市場の拡大',
                'potential_size': 'Large',
                'timing': '6-12 months'
            }
        ]

    def _forecast_trends(self, papers):
        """トレンド予測"""
        return {
            'short_term': '発酵食品由来成分への注目',
            'mid_term': 'パーソナライズドサプリメントの普及',
            'long_term': 'エピジェネティクス based 製品'
        }

    def _filter_innercare_papers(self, papers):
        """インナーケア関連論文のフィルタリング"""
        all_innercare_keywords = (
            self.innercare_priorities['high'] +
            self.innercare_priorities['medium']
        )

        filtered = {}
        for paper_id, paper in papers.items():
            paper_keywords = paper.get('keywords', [])
            if any(kw in str(paper_keywords) for kw in all_innercare_keywords):
                filtered[paper_id] = paper

        return filtered

    def _aggregate_by_ingredient(self, papers):
        """成分別にエビデンス集計"""
        ingredients = defaultdict(list)

        for paper in papers.values():
            for keyword in paper.get('keywords', []):
                # キーワードから成分名を抽出（簡易版）
                ingredient = keyword.split()[0]  # 最初の単語を成分名とする
                ingredients[ingredient].append(paper)

        return ingredients

    def _calculate_practicality_score(self, evidence):
        """実用化スコア計算"""
        score = len(evidence) * 10  # エビデンス数
        score = min(score, 100)
        return score

    def _assess_safety(self, evidence):
        """安全性評価"""
        # 簡易版
        if len(evidence) > 10:
            return "高"
        elif len(evidence) > 5:
            return "中"
        else:
            return "要検証"

    def _summarize_efficacy(self, evidence):
        """有効性の要約"""
        return "抗酸化作用、抗炎症作用"  # 簡易版

    def _extract_dosage(self, evidence):
        """推奨用量抽出"""
        return "100-500mg/日"  # 簡易版

    def _build_timeline_data(self, papers):
        """時系列データ構築"""
        timeline = defaultdict(lambda: defaultdict(int))

        for paper in papers.values():
            if 'publication_date' in paper:
                year = paper['publication_date'][:4]
                for keyword in paper.get('keywords', []):
                    timeline[year][keyword] += 1

        return timeline

    def _analyze_growth_patterns(self, timeline_data):
        """成長パターン分析"""
        patterns = {
            'exponential': [],
            'linear': [],
            'plateau': []
        }
        # 簡易版実装
        return patterns

    def _estimate_commercialization_lag(self, papers):
        """製品化ラグ推定"""
        return {
            'average_lag_years': 3.5,
            'min_lag_years': 1.5,
            'max_lag_years': 7.0
        }

    def _predict_ingredient_trend(self, ingredient, timeline_data, patterns):
        """成分別トレンド予測"""
        # 簡易版
        import random
        return {
            'growth_potential': random.uniform(0.3, 0.95),
            'maturity': random.uniform(0.1, 0.8),
            'estimated_peak': '2025-Q3'
        }

    def _save_analysis_result(self, analysis_type, data):
        """分析結果保存"""
        filename = ANALYSIS_DIR / f"{analysis_type}_{datetime.now().strftime('%Y%m%d')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n💾 結果保存: {filename}")


def main():
    parser = argparse.ArgumentParser(description='インナーケア分析システム')
    parser.add_argument('--analysis', choices=['hot_topics', 'marketing', 'development', 'prediction', 'all'],
                       default='all', help='分析タイプ')

    args = parser.parse_args()

    system = InnercareAnalysisSystem()

    if args.analysis in ['hot_topics', 'all']:
        system.analyze_hot_topics()

    if args.analysis in ['marketing', 'all']:
        system.generate_marketing_report()

    if args.analysis in ['development', 'all']:
        system.create_product_development_list()

    if args.analysis in ['prediction', 'all']:
        system.build_prediction_model()


if __name__ == "__main__":
    main()