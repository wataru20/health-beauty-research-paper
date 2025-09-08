# 韓国→日本ヒット予測システム 設計仕様書

## システム概要

韓国で流行している美容・健康関連の商品や成分が日本でヒットする確率を予測するシステム

## 予測対象カテゴリー

- 美容成分
- 栄養素
- 健康食品
- インナーケア
- インナービューティー

## 特徴量設計

### 1. 韓国YouTuber関連特徴量（初期段階）

**基本指標**
- `kr_youtuber_mention_count`: 韓国YouTuberによる言及動画数
- `kr_total_views`: 総再生数
- `kr_total_likes`: 総いいね数
- `kr_total_comments`: 総コメント数（追加提案）

**YouTuber品質指標**
- `kr_avg_subscriber_count`: 言及YouTuberの平均登録者数（追加提案）
- `kr_influencer_tier_score`: イノベーター/アーリーアダプター度合い（1-10）（追加提案）

**エンゲージメント指標**
- `kr_avg_engagement_rate`: 平均エンゲージメント率（いいね+コメント/再生数）（追加提案）
- `kr_mention_frequency`: 言及頻度（回/月）（追加提案）

### 2. 日本YouTuber関連特徴量（追従段階）

**基本指標**
- `jp_youtuber_mention_count`: 日本YouTuberによる言及動画数
- `jp_total_views`: 総再生数
- `jp_total_likes`: 総いいね数
- `jp_total_comments`: 総コメント数

**時系列指標**
- `jp_kr_time_lag_days`: 韓国言及から日本言及までの日数（追加提案）
- `jp_adoption_speed`: 日本での拡散速度（言及数/時間）（追加提案）

### 3. 日本文化適合度特徴量

**文化的受容性**
- `cultural_acceptance_score`: 日本文化適合度（1-10）
  - 例：カタツムリ成分 = 2（低い）、ヒアルロン酸 = 9（高い）
- `ingredient_familiarity`: 成分の日本での認知度（1-10）（追加提案）
- `cultural_taboo_risk`: 文化的タブーリスク（1-10）（追加提案）

**市場要因**
- `price_accessibility`: 価格アクセシビリティ（1-10）（追加提案）
- `availability_score`: 入手しやすさ（1-10）（追加提案）
- `regulatory_barrier`: 規制障壁レベル（1-10）（追加提案）

### 4. 追加提案特徴量

**季節性・タイミング**
- `seasonal_relevance`: 季節適合性（1-10）
- `launch_timing_score`: 発売タイミングの良さ（1-10）

**競合・市場環境**
- `market_saturation`: 市場飽和度（1-10）
- `similar_product_success_rate`: 類似商品の過去成功率（0-1）

**コンテンツ品質**
- `video_title_keyword_density`: 動画タイトルでのキーワード密度
- `tutorial_content_ratio`: チュートリアル系コンテンツ比率

## 予測モデル

### アルゴリズム候補

1. **ランダムフォレスト** （推奨）
   - 解釈しやすい
   - 特徴量の重要度がわかる
   - 過学習しにくい

2. **XGBoost**
   - 高精度
   - 特徴量の重要度分析が可能

3. **ロジスティック回帰**
   - シンプル
   - 係数の解釈が容易

### 出力

- `hit_probability`: ヒット確率（0-100%）
- `confidence_score`: 予測信頼度（1-10）
- `risk_factors`: リスク要因リスト
- `success_drivers`: 成功要因リスト

## システム構成

```
prediction_system/
├── data/
│   ├── training_data.json          # 訓練データ
│   └── feature_weights.json        # 特徴量重み
├── model/
│   ├── predictor.py               # 予測エンジン
│   └── trained_model.pkl          # 訓練済みモデル
├── web/
│   ├── index.html                 # メインインターフェース
│   ├── style.css                  # スタイリング
│   └── app.js                     # フロントエンド
└── api/
    └── predict_api.py             # 予測API
```

## 実装フェーズ

### Phase 1: MVP（最小実行可能製品）
- 基本特徴量での予測モデル
- シンプルなWebインターフェース
- サンプルデータでの動作確認

### Phase 2: 機能拡張
- 追加特徴量の統合
- 予測精度の向上
- UIの改善

### Phase 3: 本格運用
- リアルタイムデータ連携
- モデルの継続学習
- API化

## 質問・確認事項

1. **データ収集方法**: YouTube APIを使用した自動収集か、手動入力か？
2. **更新頻度**: モデルの再訓練頻度は？
3. **精度目標**: 何％以上の予測精度を目標とするか？
4. **ユーザー**: システムの主要利用者は？（マーケター、投資家、メーカー等）