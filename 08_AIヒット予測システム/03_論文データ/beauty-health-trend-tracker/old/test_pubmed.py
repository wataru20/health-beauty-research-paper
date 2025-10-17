#!/usr/bin/env python3
"""PubMed API接続テスト"""

from src.collectors.pubmed_collector import PubMedCollector
import os
from dotenv import load_dotenv

# 環境変数読み込み
load_dotenv()

# API接続テスト
print("="*50)
print("PubMed API接続テスト")
print("="*50)

# NCBI APIキーの状態確認
ncbi_key = os.getenv('NCBI_API_KEY')
if ncbi_key and ncbi_key != '':
    print(f"✅ NCBI APIキー: 設定済み")
else:
    print(f"⚠️  NCBI APIキー: 未設定（動作しますが、レート制限があります）")

# テスト検索実行
print("\nテスト検索を実行中...")
collector = PubMedCollector(api_key=ncbi_key)

# 最新のCOVIDワクチン論文を2件検索
pmids = collector.search_papers('COVID vaccine', max_results=2, days_back=90)

print(f"\n検索結果:")
print(f"  取得件数: {len(pmids)}件")

if pmids:
    print(f"  ✅ PubMed API連携: 正常に動作しています")
    print(f"  PMID例: {pmids}")

    # 詳細取得テスト
    print("\n詳細取得テスト中...")
    papers = collector.fetch_paper_details(pmids[:1])

    if papers and papers[0]:
        paper = papers[0]
        print(f"  ✅ 論文詳細取得: 成功")
        print(f"  タイトル: {paper.get('title', 'N/A')[:80]}...")
        print(f"  著者数: {len(paper.get('authors', []))}名")
        print(f"  発表日: {paper.get('publication_date', 'N/A')}")
        print(f"  URL: {paper.get('url', 'N/A')}")
    else:
        print(f"  ❌ 論文詳細取得: 失敗")
else:
    print(f"  ❌ PubMed API連携: 接続失敗")
    print(f"  原因: ネットワーク接続またはAPI制限の可能性があります")

print("\n現在収集済みのデータ:")
import glob
raw_files = glob.glob('data/raw/*.json')
print(f"  生データファイル数: {len(raw_files)}")
for f in sorted(raw_files)[-3:]:
    import json
    with open(f) as fp:
        data = json.load(fp)
        total = sum(len(v) if isinstance(v, list) else 0 for v in data.values())
        print(f"    - {os.path.basename(f)}: {total}件")

print("\n="*50)