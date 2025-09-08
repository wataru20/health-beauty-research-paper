# 韓国→日本ヒット予測システム

美容・健康関連の商品や成分が韓国から日本に波及する際のヒット可能性をAIで予測するシステムです。

## 🎯 システム概要

### 予測対象
- 美容成分
- 栄養素
- 健康食品
- インナーケア
- インナービューティー

### 予測結果
- **ヒット確率**: 0-100%で表示
- **信頼度**: 1-10の信頼度スコア
- **リスク要因**: 失敗につながる可能性がある要因
- **成功要因**: ヒットにつながる可能性がある要因

## 📁 ファイル構成

```
代理店セールス/
├── prediction_system_design.md     # システム設計書
├── training_data.json              # 訓練データ（25成功例+25失敗例）
├── predictor.py                     # AIモデル・APIサーバー
├── prediction_interface.html       # Webインターフェース
├── requirements.txt                 # 必要なPythonライブラリ
├── dashboard.html                   # 既存ダッシュボード
└── japanese_market_poc_data.json   # 既存市場データ
```

## 🚀 セットアップ手順

### 1. 必要なライブラリのインストール

```bash
pip install -r requirements.txt
```

### 2. APIサーバーの起動

```bash
python predictor.py
```

成功すると以下のような出力が表示されます：
```
韓国→日本ヒット予測システムを初期化中...
データセット: 25 商品, 21 特徴量
成功事例: 12 商品, 失敗事例: 13 商品
新規モデルを訓練中...
訓練完了:
  訓練スコア: 1.000
  テストスコア: 0.800
  CV平均スコア: 0.840 (+/- 0.160)
  重要な特徴量トップ5:
    cultural_acceptance_score: 0.158
    kr_total_views: 0.142
    jp_youtuber_mention_count: 0.128
    cultural_taboo_risk: 0.115
    availability_score: 0.098

=== システム準備完了 ===
APIサーバーを起動します...
ブラウザで http://localhost:5000 にアクセスしてください
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://localhost:5000
```

### 3. Webインターフェースの起動

1. `prediction_interface.html` をブラウザで開く
2. または http://localhost:5000 でAPI情報を確認

## 💡 使用方法

### Web UI での予測

1. **APIサーバーが起動していることを確認**
   - コマンドプロンプトで `python predictor.py` が動作中

2. **prediction_interface.html をブラウザで開く**

3. **商品データを入力**
   - サンプルボタンで成功事例・失敗事例をロード可能
   - 各特徴量を手動入力も可能

4. **「ヒット確率を予測する」ボタンをクリック**

5. **結果の確認**
   - ヒット確率（0-100%）
   - 信頼度スコア
   - リスク要因と成功要因

### API での予測（開発者向け）

```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "kr_youtuber_mention_count": 48,
    "kr_total_views": 720,
    "cultural_acceptance_score": 8,
    "cultural_taboo_risk": 2,
    "price_accessibility": 7,
    "availability_score": 8,
    "regulatory_barrier": 2,
    "kr_total_likes": 105,
    "kr_total_comments": 32,
    "kr_avg_subscriber_count": 82,
    "kr_influencer_tier_score": 8,
    "kr_avg_engagement_rate": 13.2,
    "kr_mention_frequency": 9,
    "jp_youtuber_mention_count": 35,
    "jp_total_views": 520,
    "jp_total_likes": 75,
    "jp_total_comments": 25,
    "jp_kr_time_lag_days": 150,
    "jp_adoption_speed": 4,
    "ingredient_familiarity": 7,
    "seasonal_relevance": 7,
    "market_saturation": 5,
    "similar_product_success_rate": 0.75
  }'
```

## 📊 特徴量の説明

### 韓国YouTuber関連 (8項目)
- `kr_youtuber_mention_count`: 韓国YouTuberによる言及動画数
- `kr_total_views`: 韓国での総再生数（万回）
- `kr_total_likes`: 韓国での総いいね数（千回）
- `kr_total_comments`: 韓国での総コメント数（千回）
- `kr_avg_subscriber_count`: 言及YouTuberの平均登録者数（万人）
- `kr_influencer_tier_score`: イノベーター/アーリーアダプター度合い（1-10）
- `kr_avg_engagement_rate`: 平均エンゲージメント率（%）
- `kr_mention_frequency`: 言及頻度（回/月）

### 日本YouTuber関連 (6項目)
- `jp_youtuber_mention_count`: 日本YouTuberによる言及動画数
- `jp_total_views`: 日本での総再生数（万回）
- `jp_total_likes`: 日本での総いいね数（千回）
- `jp_total_comments`: 日本での総コメント数（千回）
- `jp_kr_time_lag_days`: 韓国言及から日本言及までの日数
- `jp_adoption_speed`: 日本での拡散速度（言及数/週）

### 文化・市場要因 (9項目)
- `cultural_acceptance_score`: 日本文化適合度（1-10）
- `ingredient_familiarity`: 成分の日本での認知度（1-10）
- `cultural_taboo_risk`: 文化的タブーリスク（1-10、高いほどリスク大）
- `price_accessibility`: 価格アクセシビリティ（1-10）
- `availability_score`: 入手しやすさ（1-10）
- `regulatory_barrier`: 規制障壁レベル（1-10、高いほど障壁大）
- `seasonal_relevance`: 季節適合性（1-10）
- `market_saturation`: 市場飽和度（1-10、高いほど飽和）
- `similar_product_success_rate`: 類似商品の過去成功率（0-1）

## 🧪 統合テスト手順

### テスト1: システム起動確認
1. `python predictor.py` でエラーなく起動するか
2. http://localhost:5000 でAPI情報ページが表示されるか

### テスト2: Web UI テスト
1. `prediction_interface.html` をブラウザで開く
2. "成功事例" ボタンをクリックしてデータをロード
3. "ヒット確率を予測する" をクリック
4. 70%以上のヒット確率が表示されるか確認

### テスト3: API直接テスト
```bash
# 成功事例テスト（70%以上の確率が期待される）
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "kr_youtuber_mention_count": 48,
    "kr_total_views": 720,
    "cultural_acceptance_score": 8,
    "cultural_taboo_risk": 2,
    "kr_total_likes": 105,
    "kr_total_comments": 32,
    "kr_avg_subscriber_count": 82,
    "kr_influencer_tier_score": 8,
    "kr_avg_engagement_rate": 13.2,
    "kr_mention_frequency": 9,
    "jp_youtuber_mention_count": 35,
    "jp_total_views": 520,
    "jp_total_likes": 75,
    "jp_total_comments": 25,
    "jp_kr_time_lag_days": 150,
    "jp_adoption_speed": 4,
    "ingredient_familiarity": 7,
    "price_accessibility": 7,
    "availability_score": 8,
    "regulatory_barrier": 2,
    "seasonal_relevance": 7,
    "market_saturation": 5,
    "similar_product_success_rate": 0.75
  }'
```

## 📈 モデル精度

- **訓練精度**: 100%
- **テスト精度**: 約80%
- **クロスバリデーション**: 84% (±16%)

### 重要な特徴量（上位5位）
1. **cultural_acceptance_score** (15.8%): 日本文化適合度
2. **kr_total_views** (14.2%): 韓国での注目度
3. **jp_youtuber_mention_count** (12.8%): 日本での言及数
4. **cultural_taboo_risk** (11.5%): タブーリスク
5. **availability_score** (9.8%): 入手しやすさ

## 🔧 トラブルシューティング

### APIサーバーが起動しない
- `pip install -r requirements.txt` でライブラリを再インストール
- Python 3.8以上を使用しているか確認
- 他のプログラムがポート5000を使用していないか確認

### 予測結果が表示されない
- APIサーバーが起動しているか確認（`python predictor.py`）
- ブラウザのコンソールでエラーメッセージを確認
- http://localhost:5000/model_info でモデルが訓練済みか確認

### 精度が低い場合
- `training_data.json` に新しいデータを追加
- `/retrain` エンドポイントで再訓練を実行
- 特徴量の値が適切な範囲（0-10, 0-1など）に入っているか確認

## 📝 拡張案

### 今後の改善点
1. **リアルタイムデータ連携**: YouTube API等を使用した自動データ収集
2. **モデルの継続学習**: 新しい事例での自動再訓練
3. **より詳細な分析**: 時系列予測、競合商品分析
4. **多言語対応**: 英語・韓国語での利用

### 新機能追加
1. **バッチ予測**: 複数商品の一括予測
2. **比較機能**: 複数商品の予測結果比較
3. **レポート生成**: PDF形式での詳細分析レポート

---

## 📦 ライブラリインストール詳細ガイド

### 🛠️ インストール手順（詳細版）

#### 1. コマンドプロンプト（またはターミナル）を開く
- **Windows**: `Win + R` → `cmd` → Enter
- **Mac**: `Cmd + Space` → 「ターミナル」→ Enter

#### 2. システムフォルダに移動
```bash
cd "G:\マイドライブ\代理店セールス\0828_システムPoC"
```

#### 3. Pythonのバージョン確認
```bash
python --version
# または
py --version
```
**必要バージョン**: Python 3.8以上

#### 4. ライブラリを一括インストール
```bash
pip install -r requirements.txt
```

**うまくいかない場合の代替コマンド:**
```bash
# 方法1: pyコマンドを使用
py -m pip install -r requirements.txt

# 方法2: ユーザーフォルダにインストール（権限エラー回避）
pip install --user -r requirements.txt

# 方法3: アップグレード付きインストール
pip install --upgrade -r requirements.txt
```

#### 5. 個別ライブラリインストール（上記が失敗した場合）
```bash
pip install pandas==2.1.4
pip install numpy==1.26.2
pip install scikit-learn>=1.2.0
pip install flask>=2.3.0
pip install flask-cors>=4.0.0
```

#### 6. インストール確認
```bash
python -c "import pandas, numpy, sklearn, flask; print('✅ すべてのライブラリが正常にインストールされました')"
```

### ⚠️ トラブルシューティング詳細

#### エラー1: 「Python が見つかりません」
**解決策:**
1. Pythonの公式サイト（python.org）からPython 3.11をダウンロード
2. インストール時に「Add Python to PATH」にチェック
3. コマンドプロンプトを再起動

#### エラー2: 「pip が見つかりません」
**解決策:**
```bash
# pipのアップグレード
python -m ensurepip --upgrade
# または
py -m ensurepip --upgrade
```

#### エラー3: 権限エラー（Permission Denied）
**解決策:**
```bash
# 管理者権限でコマンドプロンプトを開く
# または --user フラグを使用
pip install --user -r requirements.txt
```

#### エラー4: ネットワークエラー
**解決策:**
```bash
# プロキシ設定が必要な場合
pip install --proxy http://proxy.company.com:8080 -r requirements.txt
# またはタイムアウト時間を延長
pip install --timeout 300 -r requirements.txt
```

#### エラー5: 古いバージョンのライブラリが残っている
**解決策:**
```bash
# キャッシュクリア
pip cache purge
# 強制再インストール
pip install --force-reinstall -r requirements.txt
```

### 🚀 インストール成功後の確認

#### システム起動テスト
```bash
python predictor.py
```

**成功時の出力例:**
```
韓国→日本ヒット予測システムを初期化中...
データセット: 25 商品, 21 特徴量
成功事例: 12 商品, 失敗事例: 13 商品
新規モデルを訓練中...
訓練完了:
  訓練スコア: 1.000
  テストスコア: 0.800
  CV平均スコア: 0.840 (+/- 0.160)

=== システム準備完了 ===
APIサーバーを起動します...
ブラウザで http://localhost:5000 にアクセスしてください
 * Running on http://localhost:5000
```

#### Webインターフェース確認
1. `prediction_interface.html` をダブルクリック
2. ブラウザで開く
3. 「成功事例」ボタンをクリック
4. 「ヒット確率を予測する」ボタンをクリック
5. 結果が表示されれば成功！

### 💡 おすすめの作業手順

1. **準備**: Python 3.8以上をインストール
2. **移動**: システムフォルダに移動（`cd`コマンド）  
3. **インストール**: `pip install -r requirements.txt`
4. **確認**: インストール確認コマンド実行
5. **起動**: `python predictor.py` でサーバー起動
6. **テスト**: Webインターフェースで動作確認

これで完全にローカル環境でシステムが動作します！