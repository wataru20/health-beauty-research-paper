#!/usr/bin/env python3
"""
拡張キーワード収集を実行するスクリプト
ユーザー確認なしで自動実行
"""

import sys
import os
sys.path.append(os.getcwd())
from src.expanded_keywords_collection import ExpandedDataCollection
from datetime import datetime

def main():
    print(f"""
    ====================================
    拡張キーワード収集開始
    ====================================

    開始時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """)

    collector = ExpandedDataCollection()

    # 収集規模の推定を表示
    estimation = collector.estimate_collection_size()

    print(f"""
    総キーワード数: {estimation['total_keywords']}
    推定論文数: {estimation['estimated_papers']:,}件
    推定所要時間: {estimation['estimated_time_minutes']:.1f}分

    収集を開始しています...
    """)

    # 実際の収集を実行（確認なし）
    stats = collector.run_expanded_collection()

    print(f"""
    ====================================
    収集完了
    ====================================

    終了時刻: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    収集論文数: {stats['papers_collected']}件
    """)

if __name__ == "__main__":
    main()