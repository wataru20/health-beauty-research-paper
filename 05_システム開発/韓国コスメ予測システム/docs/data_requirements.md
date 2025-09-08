# 韓国コスメヒット予測システム - 必要データ要件リスト

## 1. 市場販売データ

### 韓国市場データ
- **商品名** (Product Name)
- **ブランド名** (Brand Name)
- **カテゴリ** (Category)
  - スキンケア / メイクアップ / クレンジング / マスク・パック / ヘアケア
- **月次売上高** (Monthly Sales)
- **販売数量** (Sales Volume)
- **売上ランキング** (Sales Ranking)
- **価格帯** (Price Range)
- **販売開始日** (Launch Date)
- **販売チャネル** (Sales Channel)
  - オンライン / オフライン / 免税店

### 日本市場データ
- **同上の全項目**
- **輸入元/代理店名** (Importer/Distributor)
- **日本発売日** (Japan Launch Date)
- **日本向けローカライズ情報** (Localization Info)

## 2. YouTube分析データ

### 動画メタデータ
- **動画ID** (Video ID)
- **動画タイトル** (Title)
- **チャンネル名** (Channel Name)
- **チャンネル登録者数** (Subscribers)
- **投稿日時** (Published Date)
- **動画時間** (Duration)

### エンゲージメントデータ
- **視聴回数** (View Count)
- **いいね数** (Likes)
- **低評価数** (Dislikes)
- **コメント数** (Comment Count)
- **シェア数** (Share Count)

### コンテンツデータ
- **動画説明文** (Description)
- **タグ** (Tags)
- **サムネイル画像** (Thumbnail)
- **字幕/トランスクリプト** (Captions/Transcript)

### コメントデータ
- **コメント本文** (Comment Text)
- **コメント投稿者** (Commenter)
- **コメントいいね数** (Comment Likes)
- **返信数** (Reply Count)
- **投稿時刻** (Timestamp)

## 3. Instagram分析データ

### アカウント情報
- **アカウント名** (Account Name)
- **フォロワー数** (Followers)
- **フォロー数** (Following)
- **投稿数** (Post Count)
- **認証バッジ有無** (Verified Status)

### 投稿データ
- **投稿ID** (Post ID)
- **投稿タイプ** (Post Type)
  - フィード投稿 / リール / ストーリー / IGTV
- **投稿日時** (Posted Date)
- **キャプション** (Caption)
- **ハッシュタグ** (Hashtags)
- **メンション** (@mentions)
- **位置情報** (Location)

### エンゲージメント
- **いいね数** (Likes)
- **コメント数** (Comments)
- **保存数** (Saves)
- **シェア数** (Shares)
- **リーチ数** (Reach)
- **インプレッション数** (Impressions)
- **エンゲージメント率** (Engagement Rate)

## 4. TikTok分析データ

### 動画情報
- **動画ID** (Video ID)
- **クリエイター名** (Creator Name)
- **フォロワー数** (Followers)
- **投稿日時** (Posted Date)
- **動画時間** (Duration)

### パフォーマンス指標
- **視聴回数** (Views)
- **いいね数** (Likes)
- **コメント数** (Comments)
- **シェア数** (Shares)
- **保存数** (Saves)
- **完全視聴率** (Completion Rate)

### コンテンツ要素
- **使用楽曲** (Music/Sound Used)
- **ハッシュタグ** (Hashtags)
- **エフェクト/フィルター** (Effects/Filters)
- **動画説明文** (Caption)
- **チャレンジ参加** (Challenge Participation)

## 5. Twitter/X分析データ

### ツイート情報
- **ツイートID** (Tweet ID)
- **ユーザー名** (Username)
- **フォロワー数** (Followers)
- **投稿日時** (Posted Date)

### エンゲージメント
- **リツイート数** (Retweets)
- **いいね数** (Likes)
- **返信数** (Replies)
- **引用ツイート数** (Quote Tweets)
- **インプレッション数** (Impressions)

### コンテンツ
- **ツイート本文** (Tweet Text)
- **ハッシュタグ** (Hashtags)
- **メンション** (@mentions)
- **メディア** (Images/Videos)
- **リンク** (URLs)

## 6. テキスト分析用データ

### 品質表現ワード
- **テクスチャー表現**
  - さらさら / しっとり / もちもち / ツルツル / ふわふわ
  - 軽い / 重い / ベタつく / サラッと
  
- **効果表現**
  - 即効性 / 持続性 / 浸透力 / カバー力
  - 美白 / 保湿 / エイジングケア / 毛穴ケア
  
- **使用感表現**
  - 伸びが良い / 肌なじみ / 香り / 刺激

### センチメント指標
- **ポジティブワード**
  - 最高 / 神 / リピ確定 / 手放せない
  
- **ネガティブワード**
  - 合わない / かぶれ / 期待外れ / 高すぎ

- **中立ワード**
  - 普通 / まあまあ / 可もなく不可もなく

## 7. インフルエンサーデータ

### プロフィール情報
- **インフルエンサー名** (Name)
- **プラットフォーム** (Platform)
- **フォロワー数** (Followers)
- **平均エンゲージメント率** (Avg Engagement)
- **投稿頻度** (Posting Frequency)
- **専門分野** (Expertise Area)

### コラボレーション情報
- **提携ブランド** (Partner Brands)
- **PR投稿数** (Sponsored Posts)
- **案件単価** (Rate per Post)
- **過去の成功事例** (Success Cases)

## 8. トレンド関連データ

### 検索トレンド
- **Google Trends データ**
  - 検索ボリューム
  - 関連キーワード
  - 地域別関心度
  
- **Naver Trends データ** (韓国)
  - 検索順位
  - 急上昇キーワード

### 季節性データ
- **季節要因** (Seasonal Factors)
- **イベント連動** (Event Correlation)
  - バレンタイン / ホワイトデー / クリスマス
- **気候影響** (Weather Impact)

## 9. 競合分析データ

### 競合商品情報
- **競合ブランド** (Competitor Brands)
- **類似商品** (Similar Products)
- **価格比較** (Price Comparison)
- **差別化要素** (Differentiation Points)

### マーケットシェア
- **市場占有率** (Market Share)
- **成長率** (Growth Rate)
- **顧客ロイヤリティ** (Customer Loyalty)

## 10. 消費者属性データ

### デモグラフィック
- **年齢層** (Age Groups)
  - 10代 / 20代 / 30代 / 40代 / 50代以上
- **性別** (Gender)
- **居住地域** (Location)
- **所得水準** (Income Level)

### サイコグラフィック
- **ライフスタイル** (Lifestyle)
- **購買動機** (Purchase Motivation)
- **ブランド選好** (Brand Preference)
- **情報収集チャネル** (Information Sources)

## データ収集ツール/API要件

### 必須API
1. **YouTube Data API v3**
2. **Instagram Basic Display API / Instagram Graph API**
3. **TikTok API**
4. **Twitter API v2**
5. **Google Trends API**

### データ収集ツール
1. **Social Blade** - インフルエンサー分析
2. **Brand24** - ブランドモニタリング
3. **Hootsuite Insights** - SNS統合分析
4. **BuzzSumo** - コンテンツ分析
5. **Brandwatch** - 消費者インサイト

### 分析ツール
1. **Python ライブラリ**
   - pandas (データ処理)
   - scikit-learn (機械学習)
   - transformers (自然言語処理)
   - plotly (可視化)
   
2. **テキスト分析**
   - MeCab/Janome (日本語形態素解析)
   - KoNLPy (韓国語形態素解析)
   - TextBlob/VADER (センチメント分析)

## データ更新頻度

- **リアルタイム**: SNSエンゲージメント
- **日次**: 検索トレンド、投稿データ
- **週次**: インフルエンサー分析
- **月次**: 売上データ、市場シェア
- **四半期**: 消費者属性、競合分析