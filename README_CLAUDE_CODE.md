# 🧬 美容・健康成分トレンド追跡システム
## Mac環境 + Claude Code 実行ガイド

このプロジェクトは、PubMedから美容・健康関連の論文を自動収集し、AIで要約・分析してトレンドを可視化するシステムです。

## 📦 ファイル構成

```
beauty-health-trend-tracker/
├── src/                        # ソースコード
│   ├── main_local.py           # メイン実行ファイル
│   ├── local_dashboard.py      # ダッシュボードサーバー
│   ├── collectors/             # データ収集モジュール
│   └── analyzers/              # 分析モジュール
├── configs/                    # 設定ファイル
│   └── keywords.json           # 検索キーワード
├── requirements-local.txt      # Python依存パッケージ
├── .env.example               # 環境変数テンプレート
├── setup_local.sh             # セットアップスクリプト
└── mac_quickstart.sh          # Mac用クイックスタート
```

## 🚀 Claude Codeでの実行手順

### 1. プロジェクトをダウンロード
このZIPファイルをダウンロードして、適当なフォルダに解凍してください。

### 2. Claude Codeで開く
```bash
# ターミナルで解凍したフォルダに移動
cd ~/Downloads/beauty-health-trend-tracker

# Claude Codeで開く
claude-code .
```

### 3. セットアップ実行
Claude Codeのターミナルで以下を実行：

```bash
# セットアップスクリプトに実行権限を付与
chmod +x setup_local.sh mac_quickstart.sh

# クイックスタートを実行
./mac_quickstart.sh
```

### 4. APIキーの設定

#### Gemini API キー（必須）
1. https://makersuite.google.com/app/apikey にアクセス
2. 「Get API Key」→「Create API Key」をクリック
3. 生成されたキーをコピー

#### .envファイルを編集
```bash
# Claude Code内で編集
nano .env

# または VSCode風に
code .env
```

以下の行を編集：
```
GEMINI_API_KEY=ここに取得したAPIキーを貼り付け
```

### 5. 実行

#### 方法A: 簡単実行（推奨）
```bash
# データ収集と分析を実行
./run.sh

# 別のターミナルタブでダッシュボードを起動
./run_dashboard.sh
```

#### 方法B: 詳細制御
```bash
# 仮想環境を有効化
source venv/bin/activate

# データ収集のみ
python src/main_local.py --mode collect

# 分析のみ
python src/main_local.py --mode analyze

# すべて実行
python src/main_local.py --mode all

# ダッシュボード起動
python src/local_dashboard.py
```

### 6. ダッシュボード表示
ブラウザで http://localhost:8080 を開く

## 📊 実行結果の確認

### ログファイル
```bash
# 実行ログを確認
tail -f logs/tracker.log
```

### データファイル
```bash
# 収集したデータを確認
ls -la data/raw/
ls -la data/processed/
ls -la data/trends/
```

## ⏰ 定期実行（オプション）

### 自動実行を開始
```bash
# 週次実行（毎週月曜日 9:00）
./run_schedule.sh
```

### バックグラウンド実行
```bash
# tmuxを使う場合
tmux new -s trend-tracker
./run_schedule.sh
# Ctrl+B, D でデタッチ

# 再度アタッチ
tmux attach -t trend-tracker
```

## 🔧 トラブルシューティング

### Python3が見つからない
```bash
# Homebrewでインストール
brew install python3
```

### pipパッケージのインストールエラー
```bash
# pipをアップグレード
pip install --upgrade pip

# 個別にインストール
pip install requests
pip install google-generativeai
pip install Flask
pip install python-dotenv
pip install schedule
```

### ポート8080が使用中
.envファイルで別のポートに変更：
```
DASHBOARD_PORT=8081
```

### APIキーエラー
- .envファイルのキーが正しいか確認
- キーの前後にスペースがないか確認
- 引用符は不要です

## 📈 カスタマイズ

### キーワードを変更
`configs/keywords.json`を編集

### 収集頻度を変更
`.env`ファイルで調整：
```
DAYS_BACK=7              # 1週間分
MAX_PAPERS_PER_KEYWORD=3 # 論文数を減らす
```

## 💡 Claude Codeの便利な使い方

### ファイル編集
- `Cmd+P`: ファイル検索
- `Cmd+Shift+P`: コマンドパレット
- `Cmd+S`: 保存

### ターミナル操作
- `Cmd+J`: ターミナル表示/非表示
- `Cmd+Shift+^`: 新しいターミナル

### デバッグ
```bash
# Pythonデバッグモード
python -m pdb src/main_local.py --mode all
```

## 📞 サポート

問題が発生した場合：
1. `logs/tracker.log`を確認
2. エラーメッセージをClaude Codeに貼り付けて質問
3. GitHubのIssuesに投稿

## 🎉 これで準備完了！

Claude Codeを使えば、コード編集とターミナル操作が統合された環境で快適に実行できます。

まずは`./mac_quickstart.sh`を実行してセットアップを完了させてください！
