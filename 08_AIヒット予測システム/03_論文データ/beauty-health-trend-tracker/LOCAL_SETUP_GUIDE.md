# 📋 ローカル環境実行ガイド

## 🎯 はじめに

このガイドでは、美容・健康成分トレンド追跡システムをローカル環境（あなたのPC）で実行する方法を説明します。

## 📦 必要なソフトウェア

### 1. Python（必須）
- **バージョン**: 3.8以上
- **ダウンロード**: https://www.python.org/downloads/
- インストール時に「Add Python to PATH」にチェックを入れてください

### 2. Git（推奨）
- **ダウンロード**: https://git-scm.com/downloads
- コードをダウンロードするために使用

---

## 🚀 クイックスタート（5分で完了）

### Windows ユーザー向け

```cmd
# 1. コードをダウンロード
git clone https://github.com/YOUR_USERNAME/beauty-health-trend-tracker.git
cd beauty-health-trend-tracker

# 2. セットアップスクリプトを実行
setup_local.bat

# 3. APIキーを設定（メモ帳で.envファイルを編集）
notepad .env

# 4. システムを実行
run_tracker.bat

# 5. ダッシュボードを表示
run_dashboard.bat
```

### Mac/Linux ユーザー向け

```bash
# 1. コードをダウンロード
git clone https://github.com/YOUR_USERNAME/beauty-health-trend-tracker.git
cd beauty-health-trend-tracker

# 2. セットアップスクリプトを実行
chmod +x setup_local.sh
./setup_local.sh

# 3. APIキーを設定
nano .env  # またはお好みのエディタで編集

# 4. システムを実行
./run.sh

# 5. ダッシュボードを表示（別ターミナルで）
source venv/bin/activate
python src/local_dashboard.py
```

---

## 📝 詳細セットアップ手順

### ステップ1: プロジェクトのダウンロード

#### Gitを使う場合（推奨）
```bash
git clone https://github.com/YOUR_USERNAME/beauty-health-trend-tracker.git
cd beauty-health-trend-tracker
```

#### Gitを使わない場合
1. GitHubページの「Code」→「Download ZIP」をクリック
2. ZIPファイルを解凍
3. 解凍したフォルダに移動

### ステップ2: Python仮想環境の作成

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate
```

### ステップ3: 依存パッケージのインストール

```bash
pip install -r requirements-local.txt
```

### ステップ4: APIキーの取得と設定

#### Gemini API キー（必須）
1. [Google AI Studio](https://makersuite.google.com/app/apikey)にアクセス
2. Googleアカウントでログイン
3. 「Get API Key」→「Create API Key」をクリック
4. 生成されたキーをコピー

#### NCBI API キー（オプション、推奨）
1. [NCBI](https://www.ncbi.nlm.nih.gov/account/)でアカウント作成
2. ログイン後、Settings → API Key Management
3. 「Create an API Key」をクリック
4. 生成されたキーをコピー

#### .envファイルの編集
```env
# API Keys
GEMINI_API_KEY=ここにGeminiのAPIキーを貼り付け
NCBI_API_KEY=ここにNCBIのAPIキーを貼り付け  # オプション

# Settings
DAYS_BACK=30                    # 何日前までの論文を検索するか
MAX_PAPERS_PER_KEYWORD=5        # キーワードあたりの最大論文数
ENABLE_DASHBOARD=true           # ダッシュボード機能を有効化
DASHBOARD_PORT=8080             # ダッシュボードのポート番号
AUTO_OPEN_BROWSER=true          # ブラウザを自動で開く

# Data Storage
DATA_DIR=./data                 # データ保存先
BACKUP_DIR=./backups            # バックアップ保存先
```

---

## 🎮 使い方

### 1. 手動実行（今すぐ実行）

#### すべての処理を実行
```bash
# Windows
venv\Scripts\activate
python src\main_local.py --mode all

# Mac/Linux
source venv/bin/activate
python src/main_local.py --mode all
```

#### 論文収集のみ
```bash
python src/main_local.py --mode collect
```

#### 分析のみ（収集済みデータを使用）
```bash
python src/main_local.py --mode analyze
```

### 2. 自動実行（定期実行）

#### 週次実行（毎週月曜日 9:00）
```bash
python src/main_local.py --mode schedule --schedule-type weekly
```

#### 日次実行（毎日 9:00）
```bash
python src/main_local.py --mode schedule --schedule-type daily
```

#### テスト用（1時間ごと）
```bash
python src/main_local.py --mode schedule --schedule-type hourly
```

**注意**: 自動実行中はターミナルを閉じないでください。バックグラウンド実行したい場合は以下を参照。

### 3. ダッシュボード表示

```bash
# サーバー起動
python src/local_dashboard.py

# ブラウザで以下にアクセス
http://localhost:8080
```

---

## 🖥️ バックグラウンド実行

### Windows (タスクスケジューラ)

1. タスクスケジューラを開く（Win+R → taskschd.msc）
2. 「基本タスクの作成」をクリック
3. 名前: "Trend Tracker"
4. トリガー: 週次、月曜日 9:00
5. 操作: プログラムの開始
6. プログラム: `C:\path\to\venv\Scripts\python.exe`
7. 引数: `C:\path\to\src\main_local.py --mode all`

### Mac (launchd)

`~/Library/LaunchAgents/com.trendtracker.plist`を作成:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.trendtracker</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/venv/bin/python</string>
        <string>/path/to/src/main_local.py</string>
        <string>--mode</string>
        <string>all</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
</dict>
</plist>
```

登録:
```bash
launchctl load ~/Library/LaunchAgents/com.trendtracker.plist
```

### Linux (cron)

```bash
# crontabを編集
crontab -e

# 以下を追加（毎週月曜日 9:00）
0 9 * * 1 /path/to/venv/bin/python /path/to/src/main_local.py --mode all
```

---

## 📊 データの確認

### ファイル構造
```
data/
├── raw/                  # 生の論文データ
│   └── papers_YYYYMMDD_HHMMSS.json
├── processed/            # AI要約済みデータ
│   ├── summarized_YYYYMMDD_HHMMSS.json
│   └── latest_papers.json
└── trends/              # トレンド分析結果
    ├── analysis_YYYYMMDD_HHMMSS.json
    └── latest_analysis.json
```

### ログファイル
```
logs/
└── tracker.log          # 実行ログ
```

---

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. 「Pythonが見つかりません」エラー
**解決方法:**
- Pythonが正しくインストールされているか確認
- 環境変数PATHにPythonが追加されているか確認
- `python --version`または`python3 --version`で確認

#### 2. 「pip: command not found」エラー
**解決方法:**
```bash
# Pythonと一緒にpipをインストール
python -m ensurepip --upgrade
```

#### 3. Gemini APIエラー
**症状:** `API key not valid`
**解決方法:**
- .envファイルのAPIキーが正しいか確認
- キーの前後に余分なスペースがないか確認
- 新しいキーを生成して再試行

#### 4. 論文が見つからない
**症状:** 0件の論文
**解決方法:**
- インターネット接続を確認
- キーワードを英語に変更
- `DAYS_BACK`の値を増やす（例: 60）

#### 5. ダッシュボードが表示されない
**解決方法:**
- ポート8080が使用されていないか確認
- ファイアウォール設定を確認
- 別のポートを試す（.envで`DASHBOARD_PORT=8081`）

---

## 💾 データのバックアップと復元

### 手動バックアップ
```bash
# Windows
xcopy /E /I data backups\backup_%date:~0,4%%date:~5,2%%date:~8,2%

# Mac/Linux
cp -r data backups/backup_$(date +%Y%m%d)
```

### 自動バックアップ
システムは毎週月曜日に自動でバックアップを作成します。

### 復元
```bash
# バックアップから復元
cp -r backups/backup_20240101/* data/
```

---

## 🚀 パフォーマンス最適化

### 1. 処理速度の向上
```python
# .envファイルで調整
MAX_PAPERS_PER_KEYWORD=3  # 論文数を減らす
DAYS_BACK=7               # 期間を短くする
```

### 2. メモリ使用量の削減
- 不要なブラウザタブを閉じる
- 他のアプリケーションを終了する

### 3. API使用量の管理
- Gemini API: 1日100万トークンまで無料
- NCBI API: APIキー使用で10リクエスト/秒

---

## 📈 カスタマイズ

### キーワードの変更
`configs/keywords.json`を編集:

```json
{
  "priority_keywords": [
    "your_keyword_1",
    "your_keyword_2"
  ]
}
```

### 分析頻度の変更
`src/main_local.py`の`schedule_jobs`メソッドを編集

### ダッシュボードのカスタマイズ
`src/local_dashboard.py`のHTMLテンプレートを編集

---

## 🆘 サポート

### ログの確認
```bash
# 最新のログを表示
tail -n 100 logs/tracker.log

# エラーのみ表示
grep ERROR logs/tracker.log
```

### デバッグモード
```bash
# 詳細なログを出力
python src/main_local.py --mode all --debug
```

### コミュニティ
- GitHub Issues でバグ報告
- Discussions で質問や提案

---

## 🎉 まとめ

これで、あなたのPCで美容・健康成分のトレンドを自動追跡できるようになりました！

**主な機能:**
- ✅ PubMed論文の自動収集
- ✅ AI（Gemini）による要約
- ✅ トレンド分析
- ✅ ビジュアルダッシュボード
- ✅ 定期自動実行

**次のステップ:**
1. より多くのキーワードを追加
2. 分析結果をエクスポート
3. 他のデータソースを追加

ご質問やご提案があれば、お気軽にお問い合わせください！
