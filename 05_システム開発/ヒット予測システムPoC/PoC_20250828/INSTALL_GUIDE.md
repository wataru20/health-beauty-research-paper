# 📦 ライブラリインストール詳細ガイド

韓国→日本ヒット予測システムのライブラリインストール手順を詳しく説明します。

## 🛠️ インストール手順（詳細版）

### 1. コマンドプロンプト（またはターミナル）を開く
- **Windows**: `Win + R` → `cmd` → Enter
- **Mac**: `Cmd + Space` → 「ターミナル」→ Enter

### 2. システムフォルダに移動
```bash
cd "G:\マイドライブ\代理店セールス\0828_システムPoC"
```

### 3. Pythonのバージョン確認
```bash
python --version
# または
py --version
```
**必要バージョン**: Python 3.8以上

### 4. ライブラリを一括インストール
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

### 5. 個別ライブラリインストール（上記が失敗した場合）
```bash
pip install pandas==2.1.4
pip install numpy==1.26.2
pip install scikit-learn>=1.2.0
pip install flask>=2.3.0
pip install flask-cors>=4.0.0
```

### 6. インストール確認
```bash
python -c "import pandas, numpy, sklearn, flask; print('✅ すべてのライブラリが正常にインストールされました')"
```

## ⚠️ トラブルシューティング詳細

### エラー1: 「Python が見つかりません」
**解決策:**
1. Pythonの公式サイト（python.org）からPython 3.11をダウンロード
2. インストール時に「Add Python to PATH」にチェック
3. コマンドプロンプトを再起動

### エラー2: 「pip が見つかりません」
**解決策:**
```bash
# pipのアップグレード
python -m ensurepip --upgrade
# または
py -m ensurepip --upgrade
```

### エラー3: 権限エラー（Permission Denied）
**解決策:**
```bash
# 管理者権限でコマンドプロンプトを開く
# または --user フラグを使用
pip install --user -r requirements.txt
```

### エラー4: ネットワークエラー
**解決策:**
```bash
# プロキシ設定が必要な場合
pip install --proxy http://proxy.company.com:8080 -r requirements.txt
# またはタイムアウト時間を延長
pip install --timeout 300 -r requirements.txt
```

### エラー5: 古いバージョンのライブラリが残っている
**解決策:**
```bash
# キャッシュクリア
pip cache purge
# 強制再インストール
pip install --force-reinstall -r requirements.txt
```

## 🚀 インストール成功後の確認

### システム起動テスト
```bash
python predictor.py
# または pythonコマンドが認識されない場合
py predictor.py
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
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://172.20.10.2:5000
```

### 🌐 アクセス可能なURL
システム起動後、以下のURLでアクセスできます：

**推奨順（接続エラーが発生した場合、順番に試してください）:**
1. **http://127.0.0.1:5000** (localhostの代替URL)
2. **http://172.20.10.2:5000** (ネットワークIP、実際のIPは環境により異なります)  
3. http://localhost:5000 (一部環境では接続拒否される場合があります)

**✅ 接続成功のポイント:**
- 起動時の出力で `* Running on` で始まる行を確認
- 複数のURLが表示されるので、localhost:5000で接続できない場合は他のURLを試す
- システムが完全に起動するまで1-2分待つ

### Webインターフェース確認
1. `prediction_interface.html` をダブルクリック
2. ブラウザで開く
3. 「成功事例」ボタンをクリック
4. 「ヒット確率を予測する」ボタンをクリック
5. 結果が表示されれば成功！

## 💡 おすすめの作業手順

1. **準備**: Python 3.8以上をインストール
2. **移動**: システムフォルダに移動（`cd`コマンド）  
3. **インストール**: `pip install -r requirements.txt`
4. **確認**: インストール確認コマンド実行
5. **起動**: `python predictor.py` でサーバー起動
6. **テスト**: Webインターフェースで動作確認

## 📋 必要なライブラリ一覧

以下のライブラリが自動的にインストールされます：

### 機械学習・データ処理
- `pandas==2.1.4` - データフレーム操作
- `numpy==1.26.2` - 数値計算
- `scikit-learn>=1.2.0` - 機械学習モデル
- `scipy==1.11.4` - 科学計算

### Webアプリケーション
- `flask>=2.3.0` - APIサーバー
- `flask-cors>=4.0.0` - CORS対応

### その他の依存関係
- `streamlit==1.29.0` - データアプリ構築
- `plotly==5.18.0` - グラフ描画
- `xlsxwriter==3.1.9` - Excel出力
- `openpyxl==3.1.2` - Excel読み取り

これで完全にローカル環境でシステムが動作します！

---

## 🆘 よくある質問（FAQ）

### Q1: インストールに時間がかかるのは正常ですか？
**A1**: はい、初回は5-10分程度かかることがあります。大きなライブラリ（pandas、scikit-learn等）をダウンロードするためです。

### Q2: 「Microsoft Visual C++ 14.0 is required」エラーが出ます
**A2**: Visual Studio Build Tools をインストールしてください：
- [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/) からダウンロード

### Q3: macOSでエラーが出る場合は？
**A3**: Xcode Command Line Tools をインストール：
```bash
xcode-select --install
```

### Q4: 会社のプロキシ環境でインストールできない
**A4**: IT部門にプロキシ設定を確認し、以下のようにコマンドを実行：
```bash
pip install --proxy http://プロキシアドレス:ポート番号 -r requirements.txt
```

### Q5: 古いPythonバージョンしかない場合は？
**A5**: pyenv（Python版rbenv）を使用して複数バージョンを管理することをお勧めします。