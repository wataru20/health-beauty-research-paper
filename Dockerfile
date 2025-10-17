# Python 3.11 スリムイメージを使用
FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# 依存関係ファイルをコピー
COPY requirements.txt .

# 依存関係をインストール
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY src/ ./src/
COPY configs/ ./configs/
COPY dashboard/ ./dashboard/

# データディレクトリを作成
RUN mkdir -p data/raw data/processed data/trends

# Cloud Run用のポート設定（ダッシュボード用）
ENV PORT=8080
EXPOSE 8080

# 実行コマンド
CMD exec python src/cloud_run_app.py
