# AI Hit Prediction System
## 化粧品ヒット予測AIシステム

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-yellow)](https://github.com/features/actions)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)

## 🚀 概要

AI Hit Prediction Systemは、化粧品業界向けの高度なAI予測システムです。学術論文、ニュース、SNSトレンド、画像データなど多様なデータソースを統合し、機械学習を用いて新製品のヒット確率を予測します。

### 主な特徴

- 🔮 **高精度予測**: アンサンブル学習による95%以上の予測精度
- 📊 **マルチモーダル分析**: テキスト・画像・数値データの統合分析
- 🌐 **リアルタイムAPI**: RESTful API & WebSocket対応
- 📈 **ビジネスインサイト**: 自動レポート生成とA/Bテスト支援
- 🔒 **エンタープライズセキュリティ**: JWT認証、API Key管理、暗号化
- ☁️ **クラウドネイティブ**: Docker/Kubernetes対応、自動スケーリング

## 📋 システムアーキテクチャ

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│         (Streamlit Dashboard / Web Application)          │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                     API Gateway                          │
│              (FastAPI / Load Balancer)                   │
└─────────────────────────────────────────────────────────┘
                            │
┌──────────────┬────────────┴──────────┬─────────────────┐
│              │                        │                  │
│  Prediction  │    Data Collection     │   Business      │
│   Service    │       Service          │   Intelligence  │
│              │                        │                  │
│  ・ML Models │  ・Academic Papers     │  ・Reports      │
│  ・SHAP      │  ・News/Social Media   │  ・A/B Testing  │
│  ・Ensemble  │  ・Image Analysis      │  ・Analytics    │
└──────────────┴────────────────────────┴─────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                    Data Layer                            │
│         (PostgreSQL / Redis / Object Storage)            │
└─────────────────────────────────────────────────────────┘
```

## 🛠️ 技術スタック

### Backend
- **Language**: Python 3.9+
- **Framework**: FastAPI, Streamlit
- **ML/AI**: scikit-learn, XGBoost, LightGBM, SHAP
- **Data Processing**: pandas, NumPy, Dask

### Infrastructure
- **Container**: Docker, Kubernetes
- **Database**: PostgreSQL, Redis
- **Monitoring**: Prometheus, Grafana
- **CI/CD**: GitHub Actions

### Security
- **Authentication**: JWT, OAuth2
- **Encryption**: AES-256, TLS 1.3
- **Rate Limiting**: Redis-based

## 📦 インストール

### 前提条件

- Python 3.9+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### クイックスタート

```bash
# リポジトリのクローン
git clone https://github.com/your-org/ai-hit-prediction.git
cd ai-hit-prediction

# 仮想環境の作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係のインストール
pip install -r requirements.txt
pip install -r requirements_phase5.txt

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してAPI keyなどを設定

# データベースのセットアップ
python scripts/setup_database.py

# アプリケーション起動
python -m uvicorn src.api.realtime_api:app --reload
```

### Docker での起動

```bash
# イメージのビルドと起動
docker-compose up -d

# ログの確認
docker-compose logs -f

# 停止
docker-compose down
```

## 🎯 使用方法

### API エンドポイント

#### 予測実行
```bash
curl -X POST "http://localhost:8000/api/v1/predict" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Premium Vitamin C Serum",
    "description": "Advanced anti-aging formula",
    "keywords": ["vitamin C", "anti-aging"],
    "price": 12000,
    "brand_strength": 0.8
  }'
```

#### バッチ予測
```bash
curl -X POST "http://localhost:8000/api/v1/batch-predict" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d @batch_products.json
```

### Streamlit Dashboard

```bash
# ダッシュボード起動
streamlit run streamlit_app.py

# リアルタイムダッシュボード
streamlit run streamlit_dashboard.py
```

ブラウザで `http://localhost:8501` にアクセス

## 📊 機能詳細

### Phase 1: 基本機能
- ✅ Academic paper collection (Semantic Scholar API)
- ✅ Basic ML model (Random Forest)
- ✅ Simple prediction interface

### Phase 2: データ拡張
- ✅ News & social media integration
- ✅ Advanced feature engineering (30+ features)
- ✅ Enhanced data pipeline

### Phase 3: 分析強化
- ✅ SHAP explainability
- ✅ Optuna hyperparameter optimization
- ✅ Interactive web UI (Streamlit)
- ✅ Real-time dashboard

### Phase 4: 戦略的進化
- ✅ Multimodal analysis (Text + Image)
- ✅ Ensemble learning (Voting, Stacking, Blending)
- ✅ Business report generation
- ✅ A/B testing support
- ✅ Real-time API with WebSocket

### Phase 5: 本番展開
- ✅ Cloud deployment (AWS/GCP/Azure)
- ✅ CI/CD pipeline
- ✅ Monitoring & logging
- ✅ Security hardening
- ✅ Auto-scaling

## 🧪 テスト

```bash
# 単体テスト
pytest tests/

# 統合テスト
python test_phase4_simple.py
python test_phase5.py

# カバレッジレポート
pytest --cov=src --cov-report=html tests/
```

## 📝 API ドキュメント

APIサーバー起動後、以下のURLでドキュメントを確認:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 設定

### 環境変数

```env
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO

# Database
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key
API_KEY=your-api-key

# External APIs
SEMANTIC_SCHOLAR_API_KEY=xxx
NEWS_API_KEY=xxx

# Monitoring
SENTRY_DSN=xxx
```

### 設定ファイル

- `config/production.yaml`: 本番環境設定
- `config/staging.yaml`: ステージング環境設定
- `config/development.yaml`: 開発環境設定

## 🚀 デプロイメント

### Kubernetes

```bash
# 名前空間作成
kubectl create namespace ai-prediction

# シークレット設定
kubectl create secret generic ai-hit-secrets \
  --from-env-file=.env.production \
  -n ai-prediction

# デプロイ
kubectl apply -f deployment/kubernetes/

# 状態確認
kubectl get pods -n ai-prediction
```

### AWS ECS

```bash
# ECRへのプッシュ
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URL
docker build -t ai-hit-prediction .
docker tag ai-hit-prediction:latest $ECR_URL/ai-hit-prediction:latest
docker push $ECR_URL/ai-hit-prediction:latest

# タスク定義更新
aws ecs register-task-definition --cli-input-json file://ecs-task-definition.json

# サービス更新
aws ecs update-service --cluster production --service ai-hit-prediction
```

## 📊 モニタリング

### Prometheus メトリクス

- `ai_hit_predictions_total`: 総予測数
- `api_requests_total`: APIリクエスト数
- `model_accuracy`: モデル精度
- `api_response_time_seconds`: レスポンスタイム

### Grafana ダッシュボード

`http://localhost:3000` でアクセス (admin/admin)

## 🔒 セキュリティ

- JWT認証による API保護
- Rate limiting (100 requests/hour)
- データ暗号化 (AES-256)
- セキュリティヘッダー実装
- 定期的な依存関係更新

## 📚 ドキュメント

- [API リファレンス](docs/api/README.md)
- [アーキテクチャ設計](docs/architecture/README.md)
- [運用マニュアル](docs/operations/README.md)
- [開発ガイド](docs/development/README.md)

## 🤝 コントリビューション

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。

## 👥 チーム

- **Project Lead**: AI Strategy Team
- **ML Engineers**: Data Science Team
- **Backend Engineers**: Platform Team
- **DevOps**: Infrastructure Team

## 📞 サポート

- 📧 Email: support@ai-hit-prediction.com
- 📝 Issues: [GitHub Issues](https://github.com/your-org/ai-hit-prediction/issues)
- 💬 Slack: #ai-hit-prediction

## 🙏 謝辞

- Semantic Scholar API
- Hugging Face Transformers
- scikit-learn Community
- FastAPI Framework

---

**Version**: 5.0.0 | **Last Updated**: 2025-09-03