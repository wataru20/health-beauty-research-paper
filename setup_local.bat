@echo off
setlocal enabledelayedexpansion

REM ================================
REM ローカル環境セットアップ (Windows)
REM ================================

echo ========================================
echo 美容・健康成分トレンド追跡システム
echo ローカル環境セットアップ (Windows)
echo ========================================
echo.

REM Python チェック
echo Step 1: Python環境チェック
echo ----------------------------------------

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Pythonがインストールされていません
    echo Pythonをダウンロードしてください: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [OK] Python バージョン: %PYTHON_VERSION%
echo.

REM 仮想環境の作成
echo Step 2: Python仮想環境の作成
echo ----------------------------------------

if exist venv (
    echo 既存の仮想環境を削除しています...
    rmdir /s /q venv
)

python -m venv venv
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] 仮想環境の作成に失敗しました
    pause
    exit /b 1
)

echo [OK] 仮想環境を作成しました
echo.

REM 仮想環境のアクティベート
echo Step 3: 仮想環境のアクティベート
echo ----------------------------------------

call venv\Scripts\activate.bat
echo [OK] 仮想環境をアクティベートしました
echo.

REM 依存パッケージのインストール
echo Step 4: 依存パッケージのインストール
echo ----------------------------------------

python -m pip install --upgrade pip
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] パッケージのインストールに失敗しました
    pause
    exit /b 1
)

echo [OK] 依存パッケージをインストールしました
echo.

REM 環境変数ファイルの作成
echo Step 5: 環境変数の設定
echo ----------------------------------------

if not exist .env (
    echo 環境変数ファイルを作成します...
    
    (
        echo # API Keys
        echo GEMINI_API_KEY=your_gemini_api_key_here
        echo NCBI_API_KEY=your_ncbi_api_key_here  # Optional
        echo.
        echo # Settings
        echo DAYS_BACK=30
        echo MAX_PAPERS_PER_KEYWORD=5
        echo ENABLE_DASHBOARD=true
        echo DASHBOARD_PORT=8080
        echo.
        echo # Data Storage
        echo DATA_DIR=./data
        echo BACKUP_DIR=./backups
    ) > .env
    
    echo [OK] .envファイルを作成しました
    echo [!] .envファイルにAPIキーを設定してください
) else (
    echo [OK] .envファイルは既に存在します
)
echo.

REM ディレクトリ構造の作成
echo Step 6: ディレクトリ構造の作成
echo ----------------------------------------

if not exist data\raw mkdir data\raw
if not exist data\processed mkdir data\processed
if not exist data\trends mkdir data\trends
if not exist logs mkdir logs
if not exist backups mkdir backups

echo [OK] ディレクトリ構造を作成しました
echo.

REM 実行バッチファイルの作成
echo Step 7: 実行スクリプトの作成
echo ----------------------------------------

(
    echo @echo off
    echo echo 美容・健康トレンド追跡システムを起動します...
    echo call venv\Scripts\activate
    echo python src\main.py --mode all
    echo pause
) > run_tracker.bat

echo [OK] run_tracker.batを作成しました
echo.

REM ダッシュボード起動スクリプト
(
    echo @echo off
    echo echo ダッシュボードサーバーを起動します...
    echo call venv\Scripts\activate
    echo python src\local_dashboard.py
    echo pause
) > run_dashboard.bat

echo [OK] run_dashboard.batを作成しました
echo.

REM セットアップ完了
echo ========================================
echo セットアップ完了！
echo ========================================
echo.
echo 次のステップ:
echo.
echo 1. .envファイルを編集してAPIキーを設定
echo    メモ帳で開く: notepad .env
echo.
echo    Gemini API取得: https://makersuite.google.com/app/apikey
echo    NCBI API取得: https://www.ncbi.nlm.nih.gov/account/
echo.
echo 2. システムを実行
echo    run_tracker.bat をダブルクリック
echo.
echo 3. ダッシュボードを表示
echo    run_dashboard.bat をダブルクリック
echo    ブラウザで http://localhost:8080 にアクセス
echo.

pause
