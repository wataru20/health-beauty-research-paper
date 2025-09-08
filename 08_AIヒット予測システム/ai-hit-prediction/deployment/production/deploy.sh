#!/bin/bash
#############################################
# AI Hit Prediction System - Production Deployment Script
# 本番環境デプロイメントスクリプト
#############################################

set -e  # エラー時に停止

# カラー出力
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 設定
ENVIRONMENT=${1:-production}
NAMESPACE="ai-prediction"
APP_NAME="ai-hit-prediction"
VERSION=$(git describe --tags --always)
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN} AI Hit Prediction System Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
echo -e "Version: ${YELLOW}$VERSION${NC}"
echo -e "Timestamp: ${YELLOW}$TIMESTAMP${NC}"
echo ""

# 前提条件チェック
check_prerequisites() {
    echo -e "${YELLOW}Checking prerequisites...${NC}"
    
    # Docker check
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is not installed${NC}"
        exit 1
    fi
    
    # Kubectl check
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}kubectl is not installed${NC}"
        exit 1
    fi
    
    # Environment file check
    if [ ! -f ".env.$ENVIRONMENT" ]; then
        echo -e "${RED}.env.$ENVIRONMENT file not found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Prerequisites check passed${NC}"
}

# データベースバックアップ
backup_database() {
    echo -e "${YELLOW}Creating database backup...${NC}"
    
    # PostgreSQL backup
    kubectl exec -n $NAMESPACE deployment/postgres -- \
        pg_dump -U $DB_USER $DB_NAME > backup/db_backup_$TIMESTAMP.sql
    
    # Compress backup
    gzip backup/db_backup_$TIMESTAMP.sql
    
    # Upload to S3
    aws s3 cp backup/db_backup_$TIMESTAMP.sql.gz \
        s3://ai-hit-prediction-backups/db/$TIMESTAMP/
    
    echo -e "${GREEN}✓ Database backed up${NC}"
}

# Dockerイメージのビルドとプッシュ
build_and_push_image() {
    echo -e "${YELLOW}Building Docker image...${NC}"
    
    # Build image
    docker build \
        --build-arg VERSION=$VERSION \
        --build-arg BUILD_DATE=$TIMESTAMP \
        -t $APP_NAME:$VERSION \
        -t $APP_NAME:latest \
        -f deployment/docker/Dockerfile .
    
    # Tag for registry
    docker tag $APP_NAME:$VERSION registry.example.com/$APP_NAME:$VERSION
    docker tag $APP_NAME:latest registry.example.com/$APP_NAME:latest
    
    # Push to registry
    echo -e "${YELLOW}Pushing to registry...${NC}"
    docker push registry.example.com/$APP_NAME:$VERSION
    docker push registry.example.com/$APP_NAME:latest
    
    echo -e "${GREEN}✓ Image built and pushed${NC}"
}

# Kubernetesデプロイ
deploy_to_kubernetes() {
    echo -e "${YELLOW}Deploying to Kubernetes...${NC}"
    
    # Create namespace if not exists
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    kubectl apply -f deployment/kubernetes/configmap.yaml -n $NAMESPACE
    kubectl apply -f deployment/kubernetes/secrets.yaml -n $NAMESPACE
    
    # Update deployment with new image
    kubectl set image deployment/$APP_NAME-api \
        api=registry.example.com/$APP_NAME:$VERSION \
        -n $NAMESPACE
    
    # Apply other resources
    kubectl apply -f deployment/kubernetes/service.yaml -n $NAMESPACE
    kubectl apply -f deployment/kubernetes/ingress.yaml -n $NAMESPACE
    kubectl apply -f deployment/kubernetes/hpa.yaml -n $NAMESPACE
    
    # Wait for rollout
    kubectl rollout status deployment/$APP_NAME-api -n $NAMESPACE --timeout=10m
    
    echo -e "${GREEN}✓ Deployed to Kubernetes${NC}"
}

# ヘルスチェック
health_check() {
    echo -e "${YELLOW}Running health checks...${NC}"
    
    # Get service endpoint
    ENDPOINT=$(kubectl get service $APP_NAME-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    # Wait for service to be ready
    sleep 30
    
    # Check health endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" http://$ENDPOINT/health)
    
    if [ $response -eq 200 ]; then
        echo -e "${GREEN}✓ Health check passed${NC}"
    else
        echo -e "${RED}✗ Health check failed (HTTP $response)${NC}"
        exit 1
    fi
}

# スモークテスト
smoke_test() {
    echo -e "${YELLOW}Running smoke tests...${NC}"
    
    # API endpoint test
    ENDPOINT=$(kubectl get service $APP_NAME-service -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    # Test prediction endpoint
    response=$(curl -s -X POST http://$ENDPOINT/api/v1/predict \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $API_TOKEN" \
        -d '{
            "name": "Test Product",
            "description": "Test description",
            "keywords": ["test"],
            "price": 5000
        }')
    
    if echo "$response" | grep -q "hit_probability"; then
        echo -e "${GREEN}✓ Smoke test passed${NC}"
    else
        echo -e "${RED}✗ Smoke test failed${NC}"
        echo "$response"
        exit 1
    fi
}

# モニタリング設定
setup_monitoring() {
    echo -e "${YELLOW}Setting up monitoring...${NC}"
    
    # Apply Prometheus configuration
    kubectl apply -f deployment/monitoring/prometheus-config.yaml -n $NAMESPACE
    
    # Apply Grafana dashboards
    kubectl apply -f deployment/monitoring/grafana-dashboards.yaml -n $NAMESPACE
    
    # Create alerts
    kubectl apply -f deployment/monitoring/alert-rules.yaml -n $NAMESPACE
    
    echo -e "${GREEN}✓ Monitoring configured${NC}"
}

# ロールバック機能
rollback() {
    echo -e "${RED}Rolling back deployment...${NC}"
    
    # Rollback deployment
    kubectl rollout undo deployment/$APP_NAME-api -n $NAMESPACE
    
    # Wait for rollback
    kubectl rollout status deployment/$APP_NAME-api -n $NAMESPACE
    
    echo -e "${YELLOW}Rollback completed${NC}"
}

# デプロイメント通知
send_notification() {
    local status=$1
    local message=$2
    
    # Slack notification
    curl -X POST $SLACK_WEBHOOK_URL \
        -H 'Content-Type: application/json' \
        -d "{
            \"text\": \"Deployment Notification\",
            \"attachments\": [{
                \"color\": \"$([[ $status == 'success' ]] && echo 'good' || echo 'danger')\",
                \"title\": \"AI Hit Prediction System\",
                \"text\": \"$message\",
                \"fields\": [
                    {\"title\": \"Environment\", \"value\": \"$ENVIRONMENT\", \"short\": true},
                    {\"title\": \"Version\", \"value\": \"$VERSION\", \"short\": true}
                ],
                \"footer\": \"Deployment Script\",
                \"ts\": $(date +%s)
            }]
        }"
}

# メイン処理
main() {
    # トラップ設定（エラー時のロールバック）
    trap 'rollback' ERR
    
    # 前提条件チェック
    check_prerequisites
    
    # 環境変数読み込み
    source .env.$ENVIRONMENT
    
    # デプロイ開始通知
    send_notification "info" "Deployment started for version $VERSION"
    
    # バックアップ
    backup_database
    
    # ビルドとプッシュ
    build_and_push_image
    
    # デプロイ
    deploy_to_kubernetes
    
    # ヘルスチェック
    health_check
    
    # スモークテスト
    smoke_test
    
    # モニタリング設定
    setup_monitoring
    
    # 成功通知
    send_notification "success" "Deployment completed successfully!"
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN} Deployment Completed Successfully! 🎉${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "Version: ${YELLOW}$VERSION${NC}"
    echo -e "Environment: ${YELLOW}$ENVIRONMENT${NC}"
    echo -e "Endpoint: ${YELLOW}$ENDPOINT${NC}"
    echo ""
}

# 実行
main "$@"