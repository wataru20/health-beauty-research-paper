#!/bin/bash

# ================================
# ローカル環境セットアップスクリプト
# ================================

# 色付き出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}美容・健康成分トレンド追跡システム${NC}"
echo -e "${GREEN}ローカル環境セットアップ${NC}"
echo -e "${GREEN}========================================${NC}"

# OS判定
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="Mac"
elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    OS="Windows"
else
    OS="Unknown"
fi

echo -e "\n${BLUE}検出されたOS: $OS${NC}"

# Python バージョンチェック
echo -e "\n${YELLOW}Step 1: Python環境チェック${NC}"

# Python 3.8以上が必要
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version | cut -d' ' -f2)
    PYTHON_CMD="python"
else
    echo -e "${RED}❌ Pythonがインストールされていません${NC}"
    echo -e "Pythonをインストールしてください: https://www.python.org/downloads/"
    exit 1
fi

echo -e "✅ Python バージョン: $PYTHON_VERSION"

# 仮想環境の作成
echo -e "\n${YELLOW}Step 2: Python仮想環境の作成${NC}"

if [ -d "venv" ]; then
    echo "既存の仮想環境を削除しています..."
    rm -rf venv
fi

$PYTHON_CMD -m venv venv
echo -e "✅ 仮想環境を作成しました"

# 仮想環境のアクティベート
echo -e "\n${YELLOW}Step 3: 仮想環境のアクティベート${NC}"

if [[ "$OS" == "Windows" ]]; then
    source venv/Scripts/activate 2>/dev/null || venv\\Scripts\\activate
else
    source venv/bin/activate
fi

echo -e "✅ 仮想環境をアクティベートしました"

# 依存パッケージのインストール
echo -e "\n${YELLOW}Step 4: 依存パッケージのインストール${NC}"

pip install --upgrade pip
pip install -r requirements.txt

echo -e "✅ 依存パッケージをインストールしました"

# 環境変数ファイルの作成
echo -e "\n${YELLOW}Step 5: 環境変数の設定${NC}"

if [ ! -f ".env" ]; then
    echo "環境変数ファイルを作成します..."
    
    cat > .env << 'EOL'
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
NCBI_API_KEY=your_ncbi_api_key_here  # Optional

# Settings
DAYS_BACK=30
MAX_PAPERS_PER_KEYWORD=5
ENABLE_DASHBOARD=true
DASHBOARD_PORT=8080

# Data Storage
DATA_DIR=./data
BACKUP_DIR=./backups
EOL

    echo -e "✅ .envファイルを作成しました"
    echo -e "${YELLOW}⚠️ .envファイルにAPIキーを設定してください${NC}"
else
    echo -e "✅ .envファイルは既に存在します"
fi

# ディレクトリ構造の作成
echo -e "\n${YELLOW}Step 6: ディレクトリ構造の作成${NC}"

mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/trends
mkdir -p logs
mkdir -p backups

echo -e "✅ ディレクトリ構造を作成しました"

# 実行スクリプトの作成
echo -e "\n${YELLOW}Step 7: 実行スクリプトの作成${NC}"

# Windowsバッチファイル
if [[ "$OS" == "Windows" ]]; then
    cat > run.bat << 'EOL'
@echo off
echo Starting Trend Tracker...
call venv\Scripts\activate
python src\main.py --mode all
pause
EOL
    echo -e "✅ run.batを作成しました"
fi

# Unix系シェルスクリプト
cat > run.sh << 'EOL'
#!/bin/bash
source venv/bin/activate
python src/main.py --mode all
EOL
chmod +x run.sh
echo -e "✅ run.shを作成しました"

# セットアップ完了
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}セットアップ完了！${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${BLUE}次のステップ:${NC}"
echo -e "1. .envファイルを編集してAPIキーを設定"
echo -e "   ${YELLOW}Gemini API: https://makersuite.google.com/app/apikey${NC}"
echo -e "   ${YELLOW}NCBI API: https://www.ncbi.nlm.nih.gov/account/${NC}"
echo -e ""
echo -e "2. システムを実行"
if [[ "$OS" == "Windows" ]]; then
    echo -e "   ${GREEN}run.bat${NC} をダブルクリック"
else
    echo -e "   ${GREEN}./run.sh${NC} を実行"
fi
echo -e ""
echo -e "3. ダッシュボードを表示"
echo -e "   ${BLUE}http://localhost:8080${NC} にアクセス"
