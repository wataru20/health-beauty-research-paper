#!/bin/bash

# ================================
# Mac用 クイックスタートスクリプト
# ================================

echo "================================"
echo "美容・健康トレンド追跡システム"
echo "Mac用 クイックスタート"
echo "================================"
echo ""

# Homebrewのチェック
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrewがインストールされていません"
    echo "以下のコマンドでインストールしてください:"
    echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    exit 1
fi

# Python 3のチェック
if ! command -v python3 &> /dev/null; then
    echo "Python 3をインストールしています..."
    brew install python@3.11
fi

echo "✅ Python $(python3 --version) が検出されました"

# 仮想環境の作成
echo ""
echo "📦 仮想環境を作成しています..."
python3 -m venv venv

# 仮想環境の有効化
source venv/bin/activate

# pipのアップグレード
pip install --upgrade pip

# 依存パッケージのインストール
echo ""
echo "📚 必要なパッケージをインストールしています..."
pip install -r requirements-local.txt

# ディレクトリ作成
echo ""
echo "📁 ディレクトリ構造を作成しています..."
mkdir -p data/raw data/processed data/trends
mkdir -p logs backups

# .envファイルの作成
if [ ! -f .env ]; then
    echo ""
    echo "⚙️ 環境設定ファイルを作成しています..."
    cp .env.example .env
    echo "✅ .envファイルを作成しました"
fi

# 完了メッセージ
echo ""
echo "================================"
echo "✅ セットアップ完了！"
echo "================================"
echo ""
echo "次のステップ:"
echo ""
echo "1. APIキーを取得:"
echo "   - Gemini API: https://makersuite.google.com/app/apikey"
echo "   - NCBI API (オプション): https://www.ncbi.nlm.nih.gov/account/"
echo ""
echo "2. .envファイルを編集:"
echo "   nano .env"
echo ""
echo "3. システムを実行:"
echo "   source venv/bin/activate"
echo "   python src/main_local.py --mode all"
echo ""
echo "4. ダッシュボードを表示:"
echo "   python src/local_dashboard.py"
echo "   ブラウザで http://localhost:8080 を開く"
echo ""
echo "詳細は LOCAL_SETUP_GUIDE.md を参照してください"
