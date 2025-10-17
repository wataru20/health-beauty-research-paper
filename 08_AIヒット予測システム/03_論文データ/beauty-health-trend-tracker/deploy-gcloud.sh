#!/bin/bash

# ================================
# Google Cloud デプロイスクリプト
# ================================

# 色付き出力用
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Beauty & Health Trend Tracker - Google Cloud Setup${NC}"
echo "=================================================="

# 1. プロジェクトID設定
echo -e "\n${YELLOW}Step 1: プロジェクト設定${NC}"
read -p "Google Cloud Project ID を入力してください: " PROJECT_ID
gcloud config set project $PROJECT_ID

# 2. 必要なAPIを有効化
echo -e "\n${YELLOW}Step 2: 必要なAPIを有効化${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com \
    storage-api.googleapis.com

# 3. リージョン設定
echo -e "\n${YELLOW}Step 3: リージョン設定${NC}"
REGION="asia-northeast1"  # 東京リージョン
echo "リージョン: $REGION"

# 4. Secret Manager でAPIキーを設定
echo -e "\n${YELLOW}Step 4: APIキーの設定${NC}"
echo "Gemini API キーを設定します"
read -s -p "Gemini API Key: " GEMINI_KEY
echo
echo -n "$GEMINI_KEY" | gcloud secrets create gemini-api-key \
    --data-file=- \
    --replication-policy="automatic" 2>/dev/null || \
    echo -n "$GEMINI_KEY" | gcloud secrets versions add gemini-api-key --data-file=-

echo "NCBI API キー（オプション）を設定します"
read -s -p "NCBI API Key (Enterでスキップ): " NCBI_KEY
echo
if [ ! -z "$NCBI_KEY" ]; then
    echo -n "$NCBI_KEY" | gcloud secrets create ncbi-api-key \
        --data-file=- \
        --replication-policy="automatic" 2>/dev/null || \
        echo -n "$NCBI_KEY" | gcloud secrets versions add ncbi-api-key --data-file=-
fi

# 5. Cloud Storage バケット作成（オプション）
echo -e "\n${YELLOW}Step 5: Cloud Storage設定${NC}"
read -p "Cloud Storageを使用しますか？ (y/n): " USE_GCS
if [ "$USE_GCS" = "y" ]; then
    BUCKET_NAME="${PROJECT_ID}-trend-data"
    gsutil mb -p $PROJECT_ID -l $REGION gs://$BUCKET_NAME/ 2>/dev/null || echo "バケット既存"
    echo "バケット名: $BUCKET_NAME"
fi

# 6. Cloud Runサービスのデプロイ
echo -e "\n${YELLOW}Step 6: Cloud Runへのデプロイ${NC}"
SERVICE_NAME="trend-tracker"

# Dockerfileを使用してビルド&デプロイ
gcloud run deploy $SERVICE_NAME \
    --source . \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "USE_GCS=${USE_GCS:-false}" \
    --set-env-vars "GCS_BUCKET_NAME=${BUCKET_NAME:-}" \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
    --set-secrets="NCBI_API_KEY=ncbi-api-key:latest" \
    --service-account="${PROJECT_ID}@appspot.gserviceaccount.com"

# サービスURLを取得
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format 'value(status.url)')

echo -e "\n${GREEN}Cloud Run サービスURL: $SERVICE_URL${NC}"

# 7. Cloud Scheduler設定
echo -e "\n${YELLOW}Step 7: Cloud Scheduler設定${NC}"
read -p "定期実行を設定しますか？ (y/n): " SETUP_SCHEDULER

if [ "$SETUP_SCHEDULER" = "y" ]; then
    JOB_NAME="trend-tracker-weekly"
    
    # 毎週月曜日 9:00 JST
    gcloud scheduler jobs create http $JOB_NAME \
        --location $REGION \
        --schedule "0 9 * * 1" \
        --time-zone "Asia/Tokyo" \
        --uri "${SERVICE_URL}/trigger" \
        --http-method POST \
        --headers "Content-Type=application/json" \
        --body '{"days_back":30,"max_papers":5}' \
        --attempt-deadline 600s
    
    echo -e "${GREEN}スケジューラー設定完了${NC}"
fi

# 8. 完了メッセージ
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}デプロイ完了！${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nアクセスURL:"
echo -e "  ダッシュボード: ${SERVICE_URL}/dashboard"
echo -e "  APIエンドポイント: ${SERVICE_URL}/collect"
echo -e "\n手動実行:"
echo -e "  curl -X POST ${SERVICE_URL}/collect \\"
echo -e "    -H 'Content-Type: application/json' \\"
echo -e "    -d '{\"days_back\":30,\"max_papers\":5}'"
