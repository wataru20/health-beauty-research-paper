# 美容・健康成分トレンド追跡システム

## 概要
PubMedから美容・健康関連の論文を自動収集し、AIで要約・分析してトレンドを可視化するシステムです。

## 主な機能
- 🔍 PubMed論文の自動収集（週次/月次）
- 🤖 Gemini APIによる論文要約
- 📊 トレンド分析とダッシュボード表示
- 📈 キーワード出現頻度の時系列グラフ
- 🔔 新着論文の自動通知

## システム構成
- **実行環境**: GitHub Actions
- **ダッシュボード**: GitHub Pages
- **LLM**: Google Gemini API (無料枠)
- **データストレージ**: JSONファイル（GitHubリポジトリ）
- **論文取得**: NCBI E-utilities API

## ディレクトリ構成
```
beauty-health-trend-tracker/
├── .github/
│   └── workflows/
│       └── collect_papers.yml      # 定期実行設定
├── src/
│   ├── collectors/
│   │   └── pubmed_collector.py     # PubMed API接続
│   ├── analyzers/
│   │   ├── paper_summarizer.py     # 論文要約
│   │   └── trend_analyzer.py       # トレンド分析
│   └── utils/
│       └── config.py                # 設定管理
├── data/
│   ├── raw/                        # 生データ
│   ├── processed/                  # 処理済みデータ
│   └── trends/                     # トレンド分析結果
├── dashboard/
│   ├── index.html                  # ダッシュボード
│   ├── js/
│   │   └── visualizations.js       # グラフ表示
│   └── css/
│       └── styles.css              # スタイル
├── configs/
│   └── keywords.json               # 追跡キーワード設定
├── requirements.txt                # Python依存関係
└── README.md
```

## セットアップ手順

### 1. リポジトリの設定
1. このリポジトリをForkまたはClone
2. GitHub Secretsに以下を設定：
   - `GEMINI_API_KEY`: Gemini APIキー

### 2. キーワード設定
`configs/keywords.json`で追跡したいキーワードを設定

### 3. GitHub Actions有効化
`.github/workflows/collect_papers.yml`で実行頻度を調整

### 4. GitHub Pages有効化
リポジトリSettings > Pages > Source: Deploy from a branchを選択

## 使い方

### 手動実行
```bash
python src/main.py --mode collect  # データ収集
python src/main.py --mode analyze  # 分析実行
```

### ダッシュボード表示
`https://[your-username].github.io/beauty-health-trend-tracker/dashboard/`

## トレンド追跡キーワード
- 美容・エイジングケア
- 健康維持・ウェルネス
- 心身のパフォーマンス
- ダイエット・ボディメイク
- 注目成分・コンセプト

詳細は`configs/keywords.json`を参照

## ライセンス
MIT License
