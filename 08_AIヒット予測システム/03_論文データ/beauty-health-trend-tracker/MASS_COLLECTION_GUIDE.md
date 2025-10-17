# 📚 大規模論文データ収集ガイド

## 現在の収集状況

### ✅ テスト収集成功
- **スキンケア成分カテゴリ**: 168件の論文を収集
- **期間**: 過去3年分（2021-2024）
- **成功率**: 10キーワード中10件成功

### 📊 既存データ
- **初期収集**: 144件（5年分、10キーワード）
- **テスト収集**: 168件（3年分、10キーワード）
- **合計**: 312件の論文データ

## 🚀 大量データ収集方法

### 1. 収集可能なカテゴリ（60キーワード）

```bash
# 利用可能なカテゴリを確認
python3 src/mass_collection.py --help

# カテゴリ一覧:
# - core: 基本キーワード（10個）
# - skincare_ingredients: スキンケア成分（10個）✅ 収集済み
# - anti_aging: アンチエイジング（10個）
# - beauty_supplements: 美容サプリメント（10個）
# - advanced_treatments: 先進的トリートメント（10個）
# - natural_ingredients: 天然・オーガニック成分（10個）
# - all: 全カテゴリ（60個）
```

### 2. 推奨収集戦略

#### 小規模収集（500件程度）
```bash
# アンチエイジングカテゴリ（各30件、3年分）
python3 src/mass_collection.py --category anti_aging --years 3 --max-papers 30
# 予想: 300件
```

#### 中規模収集（1,000件程度）
```bash
# 美容サプリメントカテゴリ（各50件、5年分）
python3 src/mass_collection.py --category beauty_supplements --years 5 --max-papers 50
# 予想: 500件

# 天然成分カテゴリ（各50件、5年分）
python3 src/mass_collection.py --category natural_ingredients --years 5 --max-papers 50
# 予想: 500件
```

#### 大規模収集（3,000件程度）
```bash
# 全カテゴリ（各50件、5年分）
python3 src/mass_collection.py --category all --years 5 --max-papers 50
# 予想: 3,000件
# ⚠️ 実行時間: 約30-60分
```

### 3. 収集データの保存場所

```
data/mass_collection/
├── papers_mass_YYYYMMDD_HHMMSS.json  # メインデータ
├── stats_YYYYMMDD_HHMMSS.json         # 統計情報
└── checkpoint_*.json                  # チェックポイント（10件ごと）
```

### 4. 実行例と結果

#### 次に収集すべきカテゴリ（優先順）

1. **anti_aging** - アンチエイジング関連
   ```bash
   python3 src/mass_collection.py --category anti_aging --years 5 --max-papers 40
   # 予想: 400件
   ```

2. **beauty_supplements** - 美容サプリメント
   ```bash
   python3 src/mass_collection.py --category beauty_supplements --years 5 --max-papers 40
   # 予想: 400件
   ```

3. **advanced_treatments** - 先進的治療法
   ```bash
   python3 src/mass_collection.py --category advanced_treatments --years 5 --max-papers 30
   # 予想: 300件
   ```

### 5. API制限について

#### 現在の設定
- **NCBI API**: 未設定（レート制限: 3リクエスト/秒）
- **収集速度**: 約2-3論文/秒

#### 高速化方法
NCBIアカウントでAPIキーを取得して`.env`に設定すると10リクエスト/秒に緩和されます。
```bash
# .envファイル
NCBI_API_KEY=your_api_key_here
```

### 6. 収集データの統合

収集後、複数のデータファイルを統合する場合：

```python
# 統合スクリプト例
import json
import glob

# 全データファイルを読み込み
all_data = {}
for file in glob.glob('data/mass_collection/papers_mass_*.json'):
    with open(file) as f:
        data = json.load(f)
        all_data.update(data)

# 統計
total = sum(len(papers) for papers in all_data.values())
print(f"総論文数: {total}")
print(f"キーワード数: {len(all_data)}")
```

### 7. 推定収集可能数

| 設定 | キーワード数 | 論文/キーワード | 年数 | 推定論文数 |
|------|------------|--------------|------|-----------|
| 小規模 | 10 | 20 | 3 | 200 |
| 中規模 | 20 | 30 | 5 | 600 |
| 大規模 | 60 | 50 | 5 | 3,000 |
| 最大 | 60 | 100 | 10 | 6,000 |

### 8. トラブルシューティング

#### エラーが発生した場合
- チェックポイントファイルから復旧可能
- `data/mass_collection/checkpoint_*.json`を確認

#### メモリ不足の場合
- `--max-papers`を減らす
- カテゴリを分けて実行

#### レート制限エラー
- NCBI APIキーを設定
- 実行間隔を空ける

## 📈 次のステップ

1. **収集実行**
   ```bash
   # おすすめ: アンチエイジングカテゴリ
   python3 src/mass_collection.py --category anti_aging --years 5 --max-papers 40
   ```

2. **データ確認**
   ```bash
   ls -lah data/mass_collection/
   ```

3. **ダッシュボードで確認**
   - 収集データを`data/raw/`にコピー
   - ダッシュボードを再起動
   - http://localhost:8081 でアクセス

これで数千件規模のデータ収集が可能です！