#!/usr/bin/env python3
"""
PubMedデータビューアー用サーバー
実際に収集した論文データを表示・分析するためのWebサーバー
"""

import json
import os
from flask import Flask, render_template, jsonify, send_file
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__,
            template_folder='../',
            static_folder='../static')
CORS(app)

# データベースのパス
DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'database')
MASTER_PAPERS_PATH = os.path.join(DATABASE_DIR, 'master_papers.json')

@app.route('/')
def index():
    """データビューアーのHTMLを表示"""
    return send_file(
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pubmed_data_viewer.html'),
        mimetype='text/html'
    )

@app.route('/api/raw_papers')
def get_raw_papers():
    """収集した生の論文データを返す"""
    try:
        with open(MASTER_PAPERS_PATH, 'r', encoding='utf-8') as f:
            papers = json.load(f)

        # 各論文にメタ情報を追加
        for pmid, paper in papers.items():
            # 収集日時を人間が読める形式に変換
            if 'collected_at' in paper:
                try:
                    dt = datetime.fromisoformat(paper['collected_at'])
                    paper['collected_date_formatted'] = dt.strftime('%Y年%m月%d日 %H:%M')
                except:
                    paper['collected_date_formatted'] = paper['collected_at']

            # 論文の年を抽出
            if 'publication_date' in paper:
                year = paper['publication_date'].split('-')[0]
                paper['year'] = year

        return jsonify(papers)

    except FileNotFoundError:
        return jsonify({'error': 'データファイルが見つかりません'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics')
def get_statistics():
    """データの統計情報を返す"""
    try:
        with open(MASTER_PAPERS_PATH, 'r', encoding='utf-8') as f:
            papers = json.load(f)

        # 統計情報を計算
        stats = {
            'total_papers': len(papers),
            'unique_authors': len(set(author for paper in papers.values()
                                     for author in paper.get('authors', []))),
            'unique_journals': len(set(paper.get('journal', '') for paper in papers.values()
                                      if paper.get('journal'))),
            'keywords': {},
            'years': {},
            'mesh_terms': {}
        }

        # キーワード、年、MeSHタームの集計
        for paper in papers.values():
            # キーワード集計
            for keyword in paper.get('keywords', []):
                stats['keywords'][keyword] = stats['keywords'].get(keyword, 0) + 1

            # 年別集計
            if 'publication_date' in paper:
                year = paper['publication_date'].split('-')[0]
                stats['years'][year] = stats['years'].get(year, 0) + 1

            # MeSHターム集計
            for term in paper.get('mesh_terms', []):
                stats['mesh_terms'][term] = stats['mesh_terms'].get(term, 0) + 1

        # 上位項目のみ返す
        stats['top_keywords'] = dict(sorted(stats['keywords'].items(),
                                           key=lambda x: x[1], reverse=True)[:20])
        stats['top_mesh_terms'] = dict(sorted(stats['mesh_terms'].items(),
                                             key=lambda x: x[1], reverse=True)[:20])

        # 詳細統計の削除（大きすぎるため）
        del stats['keywords']
        del stats['mesh_terms']

        return jsonify(stats)

    except FileNotFoundError:
        return jsonify({'error': 'データファイルが見つかりません'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sample_papers/<int:count>')
def get_sample_papers(count):
    """サンプルの論文データを返す"""
    try:
        with open(MASTER_PAPERS_PATH, 'r', encoding='utf-8') as f:
            papers = json.load(f)

        # 最新の論文から指定数だけ取得
        sorted_papers = sorted(papers.items(),
                             key=lambda x: x[1].get('publication_date', ''),
                             reverse=True)
        sample = dict(sorted_papers[:count])

        return jsonify(sample)

    except FileNotFoundError:
        return jsonify({'error': 'データファイルが見つかりません'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("""
    ====================================
    PubMedデータソースビューアー
    ====================================

    収集した4,251件の実際の論文データを確認できます。

    機能：
    - 論文の詳細表示
    - 年度・キーワードでのフィルタリング
    - 統計グラフ表示
    - CSVエクスポート

    """)

    # データファイルの存在確認
    if os.path.exists(MASTER_PAPERS_PATH):
        with open(MASTER_PAPERS_PATH, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        print(f"✅ データ読み込み成功: {len(papers)}件の論文")
    else:
        print("❌ データファイルが見つかりません")

    print("\nサーバー起動中: http://localhost:8082")
    print("Ctrl+C で終了\n")

    app.run(debug=True, port=8082)