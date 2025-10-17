#!/usr/bin/env python3
"""
拡張キーワードリストによる大規模論文収集システム
200+キーワードで包括的なトレンド分析データベースを構築
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import hashlib
from collections import defaultdict

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.collectors.pubmed_collector import PubMedCollector

load_dotenv()

class ExpandedDataCollection:
    def __init__(self):
        # PubMedコレクター初期化
        self.collector = PubMedCollector()

        # データベースパス
        self.db_dir = 'database'
        self.expanded_db_dir = os.path.join(self.db_dir, 'expanded_collection')
        os.makedirs(self.expanded_db_dir, exist_ok=True)

        # 拡張キーワードリスト（日本語→英語マッピング）
        self.keyword_categories = {
            "beauty_aging": {
                "skin_care": [
                    "skin beauty",
                    "skin elasticity",
                    "skin transparency",
                    "pore care",
                    "wrinkle improvement",
                    "dark spot treatment",
                    "sagging skin",
                    "skin dryness",
                    "inner dry skin",
                    "sensitive skin",
                    "acne treatment",
                    "skin whitening",
                    "skin hydration",
                    "skin barrier function"
                ],
                "anti_aging": [
                    "anti-aging",
                    "antioxidant",
                    "anti-glycation",
                    "sirtuin",
                    "telomere",
                    "cellular senescence",
                    "autophagy skin",
                    "NAD+ anti-aging",
                    "mitochondrial health"
                ],
                "parts_care": [
                    "hair care",
                    "beautiful hair",
                    "hair growth",
                    "gray hair prevention",
                    "nail care",
                    "oral care",
                    "dental health supplements"
                ]
            },
            "health_wellness": {
                "basic_functions": [
                    "immune boost",
                    "immunity enhancement",
                    "health maintenance",
                    "physical strength",
                    "nutritional supplement",
                    "lifestyle disease prevention",
                    "basal body temperature"
                ],
                "internal_environment": [
                    "gut health",
                    "intestinal flora",
                    "microbiome",
                    "probiotics gut",
                    "body warming",
                    "detoxification",
                    "blood circulation",
                    "edema reduction",
                    "lymphatic drainage"
                ],
                "health_markers": [
                    "neutral fat",
                    "cholesterol management",
                    "blood glucose",
                    "blood pressure",
                    "liver function",
                    "uric acid",
                    "triglycerides",
                    "HDL cholesterol",
                    "LDL cholesterol"
                ]
            },
            "mental_physical_performance": {
                "mental_health": [
                    "stress relief",
                    "relaxation",
                    "anxiety reduction",
                    "mental health supplements",
                    "self-esteem",
                    "mood enhancement",
                    "depression supplements",
                    "cognitive function"
                ],
                "sleep": [
                    "sleep quality",
                    "sleep onset",
                    "deep sleep",
                    "sleep interruption",
                    "morning alertness",
                    "circadian rhythm",
                    "melatonin"
                ],
                "brain_vitality": [
                    "fatigue recovery",
                    "concentration improvement",
                    "memory enhancement",
                    "brain fog",
                    "eye strain",
                    "cognitive performance",
                    "nootropics",
                    "neuroprotection"
                ],
                "body_function": [
                    "shoulder stiffness",
                    "joint care",
                    "back pain",
                    "locomotion syndrome",
                    "bone density",
                    "muscle recovery",
                    "athletic performance"
                ]
            },
            "diet_body_contouring": {
                "weight_management": [
                    "diet supplement",
                    "weight loss",
                    "body fat reduction",
                    "spot reduction",
                    "body contouring",
                    "muscle building",
                    "basal metabolism",
                    "intestinal flora diet",
                    "appetite suppression"
                ],
                "diet_methods": [
                    "intermittent fasting",
                    "meal replacement",
                    "dietary restriction",
                    "calorie restriction",
                    "time-restricted eating"
                ]
            },
            "lifecycle_gender": {
                "women": [
                    "fertility support",
                    "postpartum care",
                    "menopause",
                    "hormonal balance",
                    "PMS premenstrual syndrome",
                    "menstrual pain",
                    "feminine care",
                    "femtech",
                    "women's health"
                ],
                "men": [
                    "men's beauty",
                    "men's health",
                    "vitality decline",
                    "androgenetic alopecia",
                    "testosterone",
                    "prostate health"
                ]
            },
            "trending_ingredients": {
                "proteins": [
                    "protein supplement",
                    "soy protein",
                    "whey protein",
                    "pea protein",
                    "casein protein",
                    "plant protein",
                    "collagen peptide"
                ],
                "beauty_ingredients": [
                    "collagen supplement",
                    "hyaluronic acid oral",
                    "placenta extract",
                    "ceramide supplement",
                    "elastin",
                    "proteoglycan",
                    "silica supplement",
                    "biotin"
                ],
                "vitamins_minerals": [
                    "vitamin C supplement",
                    "vitamin B complex",
                    "vitamin D supplement",
                    "vitamin A retinol",
                    "zinc supplement",
                    "iron supplement",
                    "magnesium supplement",
                    "calcium supplement",
                    "selenium"
                ],
                "functional_ingredients": [
                    "GABA supplement",
                    "L-theanine",
                    "lutein",
                    "astaxanthin",
                    "coenzyme Q10",
                    "alpha lipoic acid",
                    "quercetin",
                    "resveratrol"
                ],
                "probiotics_fermented": [
                    "lactobacillus",
                    "bifidobacterium",
                    "butyric acid bacteria",
                    "koji fermentation",
                    "enzyme supplement",
                    "kombucha",
                    "saccharomyces",
                    "kefir"
                ],
                "plant_derived": [
                    "green juice aojiru",
                    "spirulina",
                    "moringa",
                    "dietary fiber",
                    "isoflavone",
                    "catechin",
                    "polyphenol",
                    "chlorella",
                    "turmeric curcumin",
                    "ashwagandha"
                ]
            },
            "emerging_ingredients": {
                "next_generation": [
                    "NMN nicotinamide mononucleotide",
                    "CBD cannabidiol",
                    "exosome",
                    "stem cell culture",
                    "PQQ pyrroloquinoline quinone",
                    "LPS lipopolysaccharide",
                    "equol",
                    "lactoferrin",
                    "MCT oil",
                    "NAD+ supplement",
                    "spermidine",
                    "urolithin A"
                ]
            },
            "concepts_diets": {
                "product_categories": [
                    "functional food",
                    "health food",
                    "nutraceutical",
                    "organic supplement",
                    "additive-free",
                    "medical food"
                ],
                "lifestyle": [
                    "plant-based",
                    "sustainable nutrition",
                    "ethical food",
                    "clean eating",
                    "whole food",
                    "raw food"
                ],
                "diet_methods": [
                    "low carb",
                    "sugar restriction",
                    "gluten free",
                    "ketogenic diet",
                    "paleo diet",
                    "mediterranean diet"
                ],
                "business_models": [
                    "personalized supplement",
                    "direct to consumer D2C",
                    "subscription supplement",
                    "custom nutrition"
                ]
            },
            "technology_formulation": {
                "delivery_systems": [
                    "liposome",
                    "time release",
                    "nano technology",
                    "fermentation technology",
                    "cold press extraction",
                    "bioavailability enhancement",
                    "sustained release",
                    "microencapsulation"
                ]
            }
        }

        self.collection_stats = {
            'start_time': datetime.now().isoformat(),
            'total_keywords': 0,
            'papers_collected': 0,
            'categories_processed': {},
            'errors': []
        }

    def get_all_keywords(self):
        """全キーワードをフラットなリストで取得"""
        all_keywords = []
        for category, subcategories in self.keyword_categories.items():
            for subcategory, keywords in subcategories.items():
                all_keywords.extend(keywords)
        return all_keywords

    def collect_papers_for_keyword(self, keyword, max_results=50, years=5):
        """単一キーワードで論文を収集"""
        papers = []

        # 日付範囲の設定
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years*365)

        try:
            # PubMedCollectorを使用して検索（datetimeオブジェクトを渡す）
            pmids = self.collector.search_papers(
                query=keyword,
                max_results=max_results,
                start_date=start_date,
                end_date=end_date
            )

            # 論文詳細を取得
            if pmids:
                papers = self.collector.fetch_paper_details(pmids)

                # キーワード情報を追加
                for paper in papers:
                    paper['search_keyword'] = keyword

            time.sleep(0.1)  # API制限対策

        except Exception as e:
            print(f"Error collecting papers for {keyword}: {e}")
            self.collection_stats['errors'].append({
                'keyword': keyword,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })

        return papers

    def collect_by_category(self, category_name, subcategories):
        """カテゴリー別に論文を収集"""
        category_papers = {}
        category_stats = {
            'total_keywords': 0,
            'total_papers': 0,
            'subcategories': {}
        }

        for subcategory_name, keywords in subcategories.items():
            print(f"\n  処理中: {subcategory_name}")
            subcategory_papers = []

            for keyword in keywords:
                print(f"    - {keyword}...", end='')
                papers = self.collect_papers_for_keyword(keyword)
                subcategory_papers.extend(papers)
                print(f" {len(papers)}件")

                category_stats['total_keywords'] += 1
                category_stats['total_papers'] += len(papers)

            category_papers[subcategory_name] = subcategory_papers
            category_stats['subcategories'][subcategory_name] = {
                'keywords': len(keywords),
                'papers': len(subcategory_papers)
            }

        return category_papers, category_stats

    def run_expanded_collection(self):
        """拡張キーワードリストで大規模収集を実行"""
        print(f"""
        ====================================
        拡張論文収集システム起動
        ====================================

        カテゴリー数: {len(self.keyword_categories)}
        総キーワード数: {len(self.get_all_keywords())}

        収集を開始します...
        """)

        all_papers = {}

        for category_name, subcategories in self.keyword_categories.items():
            print(f"\n■ カテゴリー: {category_name}")

            # カテゴリー別収集
            category_papers, category_stats = self.collect_by_category(
                category_name, subcategories
            )

            # 結果を保存
            category_file = os.path.join(
                self.expanded_db_dir,
                f"{category_name}_papers.json"
            )
            with open(category_file, 'w', encoding='utf-8') as f:
                json.dump(category_papers, f, ensure_ascii=False, indent=2)

            # 統計を更新
            self.collection_stats['categories_processed'][category_name] = category_stats
            self.collection_stats['total_keywords'] += category_stats['total_keywords']
            self.collection_stats['papers_collected'] += category_stats['total_papers']

            all_papers[category_name] = category_papers

            print(f"  → {category_stats['total_papers']}件の論文を収集")

        # 全体統計を保存
        self.collection_stats['end_time'] = datetime.now().isoformat()
        stats_file = os.path.join(self.expanded_db_dir, 'collection_stats.json')
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.collection_stats, f, ensure_ascii=False, indent=2)

        # マスターファイルを作成
        master_file = os.path.join(self.expanded_db_dir, 'master_expanded_papers.json')
        with open(master_file, 'w', encoding='utf-8') as f:
            json.dump(all_papers, f, ensure_ascii=False, indent=2)

        print(f"""
        ====================================
        収集完了
        ====================================

        総キーワード数: {self.collection_stats['total_keywords']}
        収集論文数: {self.collection_stats['papers_collected']}
        エラー数: {len(self.collection_stats['errors'])}

        データ保存先: {self.expanded_db_dir}
        """)

        return self.collection_stats

    def estimate_collection_size(self):
        """収集規模の推定"""
        total_keywords = len(self.get_all_keywords())
        estimated_papers = total_keywords * 30  # 1キーワードあたり平均30件と仮定
        estimated_time = (total_keywords * 0.5) / 60  # 1キーワード0.5秒として計算

        print(f"""
        ====================================
        収集規模の推定
        ====================================

        総キーワード数: {total_keywords}
        推定論文数: {estimated_papers:,}件
        推定所要時間: {estimated_time:.1f}分

        カテゴリー別内訳:
        """)

        for category, subcategories in self.keyword_categories.items():
            keyword_count = sum(len(keywords) for keywords in subcategories.values())
            print(f"  - {category}: {keyword_count}キーワード")

        return {
            'total_keywords': total_keywords,
            'estimated_papers': estimated_papers,
            'estimated_time_minutes': estimated_time
        }

if __name__ == "__main__":
    collector = ExpandedDataCollection()

    # 収集規模の推定を表示
    estimation = collector.estimate_collection_size()

    # ユーザー確認
    print("\n収集を開始しますか？ (y/n): ", end='')
    response = input().lower()

    if response == 'y':
        # 実際の収集を実行
        stats = collector.run_expanded_collection()
    else:
        print("収集をキャンセルしました。")