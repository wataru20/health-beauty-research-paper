#!/usr/bin/env python3
"""データ状況確認スクリプト"""

import json
import glob
from datetime import datetime

print("="*60)
print("データ状況確認")
print("="*60)

# 生データ確認
raw_files = sorted(glob.glob('data/raw/*.json'))
print("\n【生データファイル】")
for f in raw_files:
    with open(f) as fp:
        data = json.load(fp)
        total = sum(len(v) if isinstance(v, list) else 0 for v in data.values())
        print(f"  {f.split('/')[-1]}: {total}件")

# 処理済みデータ確認
processed_files = sorted(glob.glob('data/processed/*.json'))
print("\n【処理済みファイル】")
for f in processed_files:
    try:
        with open(f) as fp:
            data = json.load(fp)
            if isinstance(data, dict):
                total = sum(len(v) if isinstance(v, list) else 0 for v in data.values())
                print(f"  {f.split('/')[-1]}: {total}件")
            else:
                print(f"  {f.split('/')[-1]}: 不正なフォーマット")
    except:
        print(f"  {f.split('/')[-1]}: 読み込みエラー")

# latest_papers.jsonの詳細確認
print("\n【latest_papers.jsonの詳細】")
try:
    with open('data/processed/latest_papers.json') as f:
        data = json.load(f)

    print(f"データ型: {type(data)}")
    print(f"キーワード数: {len(data)}")

    total = 0
    dates = []

    for key, papers in data.items():
        if isinstance(papers, list):
            count = len(papers)
            total += count
            print(f"  {key}: {count}件")

            # 日付情報を収集
            for p in papers:
                if isinstance(p, dict):
                    if 'publication_date' in p:
                        dates.append(p['publication_date'])

                    # 最初の論文の詳細表示
                    if papers.index(p) == 0:
                        print(f"    最初の論文:")
                        print(f"      タイトル: {p.get('title', 'N/A')[:50]}...")
                        print(f"      日付: {p.get('publication_date', 'N/A')}")
                        print(f"      PMID: {p.get('pmid', 'N/A')}")
        else:
            print(f"  {key}: 不正なデータ形式")

    print(f"\n合計論文数: {total}件")

    if dates:
        dates.sort()
        print(f"日付範囲: {dates[0]} 〜 {dates[-1]}")

        # 年ごとの分布
        year_count = {}
        for d in dates:
            year = d[:4] if d else 'Unknown'
            year_count[year] = year_count.get(year, 0) + 1

        print("\n年別分布:")
        for year in sorted(year_count.keys()):
            print(f"  {year}年: {year_count[year]}件")

except Exception as e:
    print(f"エラー: {e}")

# ダッシュボードが実際に読んでいるファイル確認
print("\n【APIエンドポイント確認】")
print("ダッシュボードは以下のファイルを読み込みます:")
print("  - /api/data/full エンドポイント:")
print("    - data/processed/summarized_*.json (最新)")
print("    - data/raw/papers_*.json (最新)")
print("    - data/trends/analysis_*.json (最新)")

print("\n="*60)