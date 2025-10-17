# 🔧 テスト値置き換え計画

## 📊 現状分析

### テスト値一覧

| # | 項目 | 場所 | 現状 | 重要度 | 対策 |
|---|------|------|------|--------|------|
| 1 | 市場規模 | line:414 | random(100-1500億円) | 🔴 高 | ディープリサーチ |
| 2 | 推奨用量 | line:416 | random(5-5000mg) | 🔴 高 | 厚労省データ |
| 3 | 成長率 | line:373-378 | random(60-250%) | 🔴 高 | 実計算に変更 |
| 4 | keyFindings | line:386-399 | random(20-95%) | 🔴 高 | 論文抽出 |
| 5 | 論文日付 | line:285 | random(0-730日前) | 🟡 中 | 実データ使用 |
| 6 | 引用数/IF | line:306-307 | random | 🟡 中 | PubMed API |
| 7 | 安全性ラベル | line:417-422 | random選択 | 🟡 中 | 固定辞書 |

---

## 🎯 修正プラン（3フェーズ）

### **フェーズ1: 即座に修正可能（作業時間: 1-2時間）**

#### ✅ 1-1. 成長率の実計算化
**現状**: line:373-378
```python
base_growth = {
    '30d': random.randint(120, 250),
    '90d': random.randint(100, 200),
    '1y': random.randint(80, 180),
    '2y': random.randint(60, 160)
}[period]
```

**修正案**:
```python
# 実際の論文数から成長率を計算
def calculate_real_growth_rate(current_papers, period):
    # 前期間のデータと比較
    if period == '30d':
        prev_period_papers = [p for p in all_papers if 31 <= p['days_ago'] <= 60]
    elif period == '90d':
        prev_period_papers = [p for p in all_papers if 91 <= p['days_ago'] <= 180]
    elif period == '1y':
        prev_period_papers = [p for p in all_papers if 366 <= p['days_ago'] <= 730]
    else:
        prev_period_papers = []

    if len(prev_period_papers) > 0:
        growth_rate = int(((len(current_papers) - len(prev_period_papers)) / len(prev_period_papers)) * 100)
    else:
        growth_rate = 100

    return max(-100, min(500, growth_rate))  # -100%〜+500%に制限
```

**メリット**: 実データベース、すぐ実装可能

---

#### ✅ 1-2. 安全性ラベルの固定化
**現状**: line:417-422 ランダム選択

**修正案**:
```python
# 成分ごとの安全性データベース
safety_database = {
    'コラーゲン': '機能性表示食品届出済み',
    'ビタミンC': 'GRAS認定取得',
    'ビタミンD': '機能性表示食品届出済み',
    'プロバイオティクス': '食経験豊富',
    'NMN': '長期摂取でも安全性確認済み',
    # ... 主要20成分
}

safety = safety_database.get(topic_name, '要検証')
```

**メリット**: 正確、すぐ実装可能

---

#### ✅ 1-3. 推奨用量の固定化
**現状**: line:416 `random.randint(5, 5000)mg/日`

**修正案**:
```python
# 厚生労働省「日本人の食事摂取基準」ベース
dosage_database = {
    'ビタミンC': {'amount': 100, 'unit': 'mg/日', 'source': '厚労省2020'},
    'ビタミンD': {'amount': 8.5, 'unit': 'μg/日', 'source': '厚労省2020'},
    'ビタミンE': {'amount': 6.0, 'unit': 'mg/日', 'source': '厚労省2020'},
    '鉄': {'amount': 10.5, 'unit': 'mg/日', 'source': '厚労省2020'},
    'カルシウム': {'amount': 700, 'unit': 'mg/日', 'source': '厚労省2020'},
    'マグネシウム': {'amount': 340, 'unit': 'mg/日', 'source': '厚労省2020'},
    '亜鉛': {'amount': 11, 'unit': 'mg/日', 'source': '厚労省2020'},
    'EPA': {'amount': 1000, 'unit': 'mg/日', 'source': '日本脂質栄養学会'},
    'DHA': {'amount': 1000, 'unit': 'mg/日', 'source': '日本脂質栄養学会'},
    'コラーゲン': {'amount': 5000, 'unit': 'mg/日', 'source': '臨床試験平均'},
    'プロバイオティクス': {'amount': 1000000000, 'unit': 'CFU/日', 'source': '機能性表示食品'},
    'NMN': {'amount': 250, 'unit': 'mg/日', 'source': '臨床試験'},
    'クルクミン': {'amount': 1500, 'unit': 'mg/日', 'source': '臨床試験'},
    'ポリフェノール': {'amount': 1000, 'unit': 'mg/日', 'source': '推奨量'},
    # デフォルト値
}

dosage_info = dosage_database.get(topic_name, {'amount': 0, 'unit': 'mg/日', 'source': 'N/A'})
dosage = f"{dosage_info['amount']}{dosage_info['unit']}" if dosage_info['amount'] > 0 else 'N/A'
```

**メリット**: 公的データベース、信頼性高い

---

### **フェーズ2: ディープリサーチ後（作業時間: 5-10時間）**

#### 🔄 2-1. 市場規模の実データ化
**タスク**: DEEP_RESEARCH_PROMPT.mdを使用してリサーチ
**データソース**:
- 富士経済
- 矢野経済研究所
- TPCマーケティング

**実装**:
```python
market_size_database = {
    'コラーゲン': {'2024': 450, '2023': 420, 'source': '富士経済2024'},
    'EPA': {'2024': 350, '2023': 320, 'source': '矢野経済2024'},
    # ... リサーチ結果を追加
}

market_data = market_size_database.get(topic_name, {'2024': 0})
if market_data['2024'] > 0:
    marketSize = f"2024年予測：{market_data['2024']}億円"
else:
    # フォールバック: 論文数ベースの推定
    estimated_size = len(topic_papers) * 3  # 係数は要調整
    marketSize = f"2024年推定：{estimated_size}億円"
```

---

#### 🔄 2-2. keyFindingsの論文抽出
**タスク**: LLMで主要論文から具体的数値を抽出

**実装案**:
```python
# 論文タイトル・アブストラクトからLLMで抽出
def extract_key_findings_from_papers(papers, ingredient_name):
    # 上位3件の論文を選択
    top_papers = sorted(papers, key=lambda x: x['citations'], reverse=True)[:3]

    # LLM APIで各論文から具体的数値を抽出
    findings = []
    for paper in top_papers:
        # Gemini/GPT APIで抽出
        finding = llm_extract_finding(paper['title'], ingredient_name)
        findings.append(finding)

    return findings[:3]
```

**代替案（簡易版）**: テンプレート + 論文数ベース
```python
def generate_findings_from_data(topic_name, paper_count, clinical_trial_count):
    findings = []

    # 臨床試験が多い場合
    if clinical_trial_count > 5:
        findings.append(f'{topic_name}の有効性が{clinical_trial_count}件の臨床試験で確認')

    # 論文数が多い場合
    if paper_count > 100:
        findings.append(f'大規模研究により{topic_name}の安全性が実証')

    # メカニズム情報（固定辞書）
    mechanism = mechanism_database.get(topic_name, '詳細研究中')
    findings.append(mechanism)

    return findings[:3]
```

---

### **フェーズ3: オプション（余裕があれば）**

#### 🔵 3-1. 論文日付の実データ化
**タスク**: 元データに日付があれば使用

**実装**:
```python
# データ読み込み時に実際の日付を使用
pub_date_str = paper.get('publication_date', None)
if pub_date_str:
    pub_date = datetime.strptime(pub_date_str, '%Y-%m-%d')
    days_ago = (datetime.now() - pub_date).days
else:
    # フォールバック: ランダム割り当て
    days_ago = random.randint(1, 730)
```

---

#### 🔵 3-2. 引用数・Impact Factorの取得
**タスク**: PubMed APIまたはCrossref APIで取得

**実装**:
```python
import requests

def get_citation_count(pmid):
    # PubMed API または Semantic Scholar API
    response = requests.get(f'https://api.semanticscholar.org/v1/paper/PMID:{pmid}')
    if response.status_code == 200:
        data = response.json()
        return data.get('citationCount', 0)
    return 0
```

---

## ⏱️ 作業時間見積もり

| フェーズ | 内容 | 時間 | 難易度 |
|---------|------|------|--------|
| フェーズ1-1 | 成長率実計算 | 30分 | ⭐ |
| フェーズ1-2 | 安全性固定化 | 30分 | ⭐ |
| フェーズ1-3 | 推奨用量固定化 | 1時間 | ⭐⭐ |
| フェーズ2-1 | 市場規模リサーチ | 5-10時間 | ⭐⭐⭐⭐ |
| フェーズ2-2 | keyFindings抽出 | 2-3時間 | ⭐⭐⭐ |
| フェーズ3-1 | 論文日付実データ | 1時間 | ⭐⭐ |
| フェーズ3-2 | 引用数API取得 | 2時間 | ⭐⭐⭐ |

**合計**: 12-18時間

---

## 🚀 推奨実行順序

### **今すぐ開始（優先度：最高）**
1. ✅ フェーズ1-1: 成長率の実計算化（30分）
2. ✅ フェーズ1-2: 安全性ラベル固定化（30分）
3. ✅ フェーズ1-3: 推奨用量固定化（1時間）

→ **合計2時間で主要なテスト値を排除**

### **並行作業（ディープリサーチ中）**
- 🔄 フェーズ2-1: 市場規模のディープリサーチ（進行中）

### **リサーチ完了後**
- 🔄 フェーズ2-2: keyFindings最適化
- 🔵 フェーズ3: オプション機能

---

## 📝 次のアクション

どのフェーズから始めますか？

**推奨**: フェーズ1（1-1, 1-2, 1-3）を今すぐ実装
→ 2時間で大幅に精度向上

実装を開始しますか？
