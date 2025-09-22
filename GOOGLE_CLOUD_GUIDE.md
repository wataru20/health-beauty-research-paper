# 📋 Google Cloud 実装ガイド

## 🎯 3つの実装オプション比較

### 1. **Cloud Run** （推奨）
- **月額コスト**: 0〜500円程度
- **特徴**: Docker コンテナベース、スケーラブル、ダッシュボード付き
- **適している場合**: 本格的な運用、ダッシュボード表示、将来的な拡張

### 2. **Cloud Functions** 
- **月額コスト**: 0〜100円程度
- **特徴**: サーバーレス、最も安価、シンプル
- **適している場合**: コスト最優先、APIのみで十分、軽量な処理

### 3. **Compute Engine + Cron**
- **月額コスト**: 1,000円〜
- **特徴**: 完全なコントロール、常時稼働
- **適している場合**: 複雑な処理、他のシステムとの連携

---

## 🚀 オプション1: Cloud Run セットアップ手順

### 前提条件
- Google Cloud アカウント
- gcloud CLI インストール済み
- プロジェクト作成済み

### ステップ1: 初期設定

```bash
# gcloud CLIにログイン
gcloud auth login

# プロジェクト設定
gcloud config set project YOUR_PROJECT_ID

# 必要なAPIを有効化
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    cloudscheduler.googleapis.com \
    secretmanager.googleapis.com
```

### ステップ2: APIキーの設定

```bash
# Gemini API キーを Secret Manager に保存
echo -n "YOUR_GEMINI_API_KEY" | gcloud secrets create gemini-api-key \
    --data-file=- \
    --replication-policy="automatic"

# NCBI API キー（オプション）
echo -n "YOUR_NCBI_API_KEY" | gcloud secrets create ncbi-api-key \
    --data-file=- \
    --replication-policy="automatic"
```

### ステップ3: Cloud Run デプロイ

```bash
# リポジトリをクローン
git clone https://github.com/YOUR_USERNAME/beauty-health-trend-tracker.git
cd beauty-health-trend-tracker

# Cloud Run にデプロイ（Dockerfileを使用）
gcloud run deploy trend-tracker \
    --source . \
    --region asia-northeast1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --timeout 300 \
    --set-secrets="GEMINI_API_KEY=gemini-api-key:latest" \
    --set-secrets="NCBI_API_KEY=ncbi-api-key:latest"
```

### ステップ4: Cloud Scheduler 設定（定期実行）

```bash
# 毎週月曜日 9:00 JST に実行
gcloud scheduler jobs create http trend-tracker-weekly \
    --location asia-northeast1 \
    --schedule "0 9 * * 1" \
    --time-zone "Asia/Tokyo" \
    --uri "https://YOUR-SERVICE-URL.run.app/trigger" \
    --http-method POST \
    --headers "Content-Type=application/json"
```

---

## ⚡ オプション2: Cloud Functions セットアップ手順

### ステップ1: Functions用ファイル準備

```bash
# 新しいディレクトリ作成
mkdir trend-tracker-functions
cd trend-tracker-functions

# 必要ファイルをコピー
cp ../cloud_function.py main.py
cp ../requirements-functions.txt requirements.txt
```

### ステップ2: デプロイ

```bash
# Cloud Functions にデプロイ
gcloud functions deploy collect-trends \
    --runtime python311 \
    --trigger-http \
    --allow-unauthenticated \
    --entry-point collect_trends \
    --memory 256MB \
    --timeout 60s \
    --region asia-northeast1 \
    --set-env-vars GEMINI_API_KEY=$GEMINI_API_KEY
```

### ステップ3: 定期実行設定

```bash
# Cloud Scheduler で週次実行
gcloud scheduler jobs create http trend-function-weekly \
    --location asia-northeast1 \
    --schedule "0 9 * * 1" \
    --time-zone "Asia/Tokyo" \
    --uri "https://REGION-PROJECT.cloudfunctions.net/collect-trends" \
    --http-method POST
```

---

## 💾 Cloud Storage 連携（オプション）

### バケット作成

```bash
# データ保存用バケット作成
gsutil mb -l asia-northeast1 gs://YOUR-PROJECT-trend-data/

# Cloud Run/Functions にバケット名を設定
gcloud run services update trend-tracker \
    --update-env-vars GCS_BUCKET_NAME=YOUR-PROJECT-trend-data \
    --update-env-vars USE_GCS=true
```

### IAM権限設定

```bash
# サービスアカウントに Storage権限を付与
gcloud projects add-iam-policy-binding YOUR-PROJECT-ID \
    --member="serviceAccount:YOUR-PROJECT@appspot.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

---

## 📊 モニタリングとログ

### Cloud Runのログ確認

```bash
# 最新のログを表示
gcloud run services logs read trend-tracker \
    --region asia-northeast1 \
    --limit 50
```

### Cloud Functionsのログ確認

```bash
# 関数のログを表示
gcloud functions logs read collect-trends \
    --region asia-northeast1 \
    --limit 50
```

### Cloud Monitoring ダッシュボード

1. [Cloud Console](https://console.cloud.google.com) にアクセス
2. 「Monitoring」→「ダッシュボード」
3. 新規ダッシュボード作成
4. 以下のメトリクスを追加:
   - Cloud Run: リクエスト数、レイテンシ、エラー率
   - Functions: 実行回数、実行時間、エラー数
   - Storage: オブジェクト数、ストレージ使用量

---

## 💰 コスト管理

### 無料枠の活用

**Cloud Run 無料枠（月額）:**
- 200万リクエスト
- 360,000 GB-秒のメモリ
- 180,000 vCPU-秒のCPU

**Cloud Functions 無料枠（月額）:**
- 200万呼び出し
- 400,000 GB-秒
- 200,000 GHz-秒のCPU

**Cloud Storage 無料枠:**
- 5GB のストレージ
- 1GB のネットワーク下り

### 予算アラート設定

```bash
# 月額予算を設定（例: 1000円）
gcloud billing budgets create \
    --billing-account=YOUR-BILLING-ACCOUNT \
    --display-name="Trend Tracker Budget" \
    --budget-amount=1000JPY \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100
```

---

## 🔧 トラブルシューティング

### よくある問題と解決方法

#### 1. デプロイ失敗
```bash
# ビルドログを確認
gcloud builds list --limit=5
gcloud builds log BUILD_ID
```

#### 2. APIキーエラー
```bash
# Secret Manager の確認
gcloud secrets versions list gemini-api-key
# 権限確認
gcloud secrets get-iam-policy gemini-api-key
```

#### 3. タイムアウトエラー
```bash
# タイムアウト時間を延長
gcloud run services update trend-tracker \
    --timeout=540  # 9分に延長
```

#### 4. メモリ不足
```bash
# メモリを増やす
gcloud run services update trend-tracker \
    --memory=1Gi
```

---

## 📈 パフォーマンス最適化

### 1. コールドスタート対策
```yaml
# Cloud Run の最小インスタンス設定
gcloud run services update trend-tracker \
    --min-instances=1  # 常に1つは起動
```

### 2. 並行処理の最適化
```python
# cloud_run_app.py で並行処理数を制限
--concurrency=10  # 同時リクエスト数を制限
```

### 3. キャッシュの活用
```python
# Redisやmemcachedを使用してAPIレスポンスをキャッシュ
from google.cloud import memcache
# 実装例...
```

---

## 🔐 セキュリティベストプラクティス

1. **認証の追加**
```bash
# Cloud Run に IAM認証を設定
gcloud run services add-iam-policy-binding trend-tracker \
    --member="user:YOUR-EMAIL" \
    --role="roles/run.invoker"
```

2. **VPC接続**
```bash
# プライベートIPアドレスのみでアクセス
gcloud run services update trend-tracker \
    --vpc-connector=projects/PROJECT/locations/REGION/connectors/CONNECTOR
```

3. **監査ログ**
```bash
# Cloud Audit Logs を有効化
gcloud logging sinks create trend-tracker-audit \
    storage.googleapis.com/YOUR-AUDIT-BUCKET \
    --log-filter='resource.type="cloud_run_revision"'
```

---

## 📞 サポート

問題が発生した場合:
1. [Google Cloud ドキュメント](https://cloud.google.com/docs)
2. [Stack Overflow](https://stackoverflow.com/questions/tagged/google-cloud-platform)
3. [Google Cloud サポート](https://cloud.google.com/support)

---

## 次のステップ

1. ✅ Cloud Run または Functions をデプロイ
2. ✅ Cloud Scheduler で定期実行を設定
3. ✅ Cloud Monitoring でモニタリング
4. 🔄 必要に応じて機能拡張
   - BigQuery連携でデータ分析
   - Vertex AI でより高度な分析
   - Cloud Composer でワークフロー管理
