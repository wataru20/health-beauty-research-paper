#!/usr/bin/env python3
"""
収集データをユーザーフレンドリーな構造に整理
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

def organize_data():
    """データを整理された構造に再配置"""

    # ベースディレクトリ
    base_dir = Path(".")

    # 新しいフォルダ構造を作成
    organized_dir = base_dir / "📊_論文データベース_2024年9月"

    # メインフォルダ作成
    organized_dir.mkdir(exist_ok=True)

    # サブフォルダ構造
    folders = {
        "🔬_研究論文データ": {
            "01_美容・エイジングケア": ["database/expanded_collection/beauty_aging_papers.json"],
            "02_健康・ウェルネス": ["database/expanded_collection/health_wellness_papers.json"],
            "03_メンタル・パフォーマンス": ["database/expanded_collection/mental_physical_performance_papers.json"],
            "04_ダイエット・ボディケア": ["database/expanded_collection/diet_body_contouring_papers.json"],
            "05_ライフサイクル": ["database/expanded_collection/lifecycle_gender_papers.json"],
            "06_トレンド成分": ["database/expanded_collection/trending_ingredients_papers.json"],
            "07_新興成分": ["database/expanded_collection/emerging_ingredients_papers.json"],
            "08_コンセプト・食事法": ["database/expanded_collection/concepts_diets_papers.json"],
            "09_技術・製法": ["database/expanded_collection/technology_formulation_papers.json"]
        },
        "📈_分析レポート": {
            "インナーケア分析": ["database/innercare_analysis/"],
            "予測モデル": ["database/innercare_analysis/prediction_model_20250924.json"],
            "ホットトピック": ["database/innercare_analysis/hot_topics_20250924.json"],
            "実用化推奨": ["database/innercare_analysis/commercialization_recommendations_20250924.json"]
        },
        "🖥️_ダッシュボード": {
            "分析ダッシュボード": ["innercare_dashboard_interactive.html"],
            "データビューアー": ["pubmed_data_viewer.html"],
            "分析プロセス可視化": ["analysis_process_viewer.html"]
        },
        "📋_マスターデータ": {
            "統合データ（9,087件）": ["database/expanded_collection/master_expanded_papers.json"],
            "初期データ（4,251件）": ["database/master_papers.json"],
            "収集統計": ["database/expanded_collection/collection_stats.json"]
        }
    }

    # フォルダとファイルを整理
    for main_folder, sub_items in folders.items():
        main_path = organized_dir / main_folder
        main_path.mkdir(exist_ok=True)

        for sub_name, file_paths in sub_items.items():
            sub_path = main_path / sub_name

            for file_path in file_paths:
                src = base_dir / file_path

                if src.exists():
                    if src.is_dir():
                        # ディレクトリの場合
                        if sub_path.exists():
                            shutil.rmtree(sub_path)
                        shutil.copytree(src, sub_path)
                    else:
                        # ファイルの場合
                        sub_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, sub_path)
                    print(f"✅ コピー完了: {sub_name}")

    # README作成
    readme_content = f"""# 📊 インナーケア・健康食品トレンド論文データベース

## 概要
- **収集日**: {datetime.now().strftime('%Y年%m月%d日')}
- **総論文数**: 9,087件
- **キーワード数**: 206個
- **データ期間**: 過去5年間（2020-2025）

## 📁 フォルダ構成

### 🔬 研究論文データ
各カテゴリー別に整理された論文データ（JSON形式）

- **01_美容・エイジングケア** (1,401件)
  - スキンケア、アンチエイジング、ヘアケアなど

- **02_健康・ウェルネス** (1,243件)
  - 免疫、腸内環境、生活習慣病予防など

- **03_メンタル・パフォーマンス** (990件)
  - ストレス、睡眠、認知機能など

- **04_ダイエット・ボディケア** (497件)
  - 減量、体脂肪、筋肉増強など

- **05_ライフサイクル** (556件)
  - 妊活、更年期、男性健康など

- **06_トレンド成分** (2,396件) ⭐最多
  - コラーゲン、ビタミン、プロバイオティクスなど

- **07_新興成分** (596件)
  - NMN、CBD、エクソソームなど

- **08_コンセプト・食事法** (1,010件)
  - 機能性食品、ケトジェニック、断食など

- **09_技術・製法** (398件)
  - リポソーム、ナノ技術、発酵技術など

### 📈 分析レポート
AI分析による洞察とトレンド予測

- **インナーケア分析**: 成分別の詳細分析
- **予測モデル**: 6ヶ月〜2年後のトレンド予測
- **ホットトピック**: 急成長中のトレンド
- **実用化推奨**: 商品化推奨成分リスト

### 🖥️ ダッシュボード
ブラウザで開ける可視化ツール

- **分析ダッシュボード**: インタラクティブなトレンド表示
- **データビューアー**: 論文データの検索・閲覧
- **分析プロセス可視化**: AIの分析ロジック解説

### 📋 マスターデータ
全データの統合ファイル

- **統合データ**: 9,087件の全論文データ
- **初期データ**: 最初の4,251件
- **収集統計**: 収集プロセスの詳細記録

## 🚀 使い方

### ダッシュボードを開く
HTMLファイルをダブルクリックしてブラウザで開いてください。

### JSONデータを分析する
PythonやExcelでJSONファイルを読み込んで独自の分析が可能です。

```python
import json

# データ読み込み例
with open('📋_マスターデータ/統合データ（9,087件）', 'r') as f:
    data = json.load(f)
```

## 📊 主な成果
- NMN、CBD、エクソソームなど最新トレンドを網羅
- グルタチオン、アスタキサンチンの急成長を検出
- 腸内環境系サプリメントの長期トレンドを予測

## 💡 活用例
- 新商品開発の方向性決定
- マーケティング戦略立案
- 競合分析
- 投資判断

---
※このデータは研究目的で収集されたPubMed論文データです。
"""

    readme_path = organized_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)

    print(f"""
    ====================================
    データ整理完了！
    ====================================

    保存先: {organized_dir}

    フォルダ構成:
    📊_論文データベース_2024年9月/
    ├── 🔬_研究論文データ/（カテゴリー別）
    ├── 📈_分析レポート/（AI分析結果）
    ├── 🖥️_ダッシュボード/（可視化ツール）
    ├── 📋_マスターデータ/（統合データ）
    └── README.md（使い方ガイド）

    ダッシュボードはHTMLファイルをダブルクリックで開けます。
    """)

    return organized_dir

if __name__ == "__main__":
    organize_data()