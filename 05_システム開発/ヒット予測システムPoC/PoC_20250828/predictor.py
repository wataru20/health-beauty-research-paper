#!/usr/bin/env python3
"""
韓国→日本ヒット予測システム
機械学習モデルとAPI実装
"""

import json
import pickle
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import logging
import warnings
warnings.filterwarnings('ignore')

class HitPredictor:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2
        )
        self.scaler = StandardScaler()
        self.feature_names = []
        self.feature_importance = {}
        self.is_trained = False
        
    def load_training_data(self, filepath='training_data.json'):
        """訓練データを読み込む"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data['training_data'])
            
            # 特徴量とターゲットを分離
            feature_columns = [col for col in df.columns if col not in ['product_name', 'category', 'hit_in_japan']]
            X = df[feature_columns]
            y = df['hit_in_japan']
            
            self.feature_names = feature_columns
            return X, y, df
        except Exception as e:
            print(f"データ読み込みエラー: {e}")
            return None, None, None
    
    def train(self, X, y):
        """モデルを訓練"""
        try:
            # データを標準化
            X_scaled = self.scaler.fit_transform(X)
            
            # 訓練・テストデータに分割
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # モデル訓練
            self.model.fit(X_train, y_train)
            
            # 評価
            train_score = self.model.score(X_train, y_train)
            test_score = self.model.score(X_test, y_test)
            
            # クロスバリデーション
            cv_scores = cross_val_score(self.model, X_scaled, y, cv=5)
            
            # 特徴量重要度を取得
            self.feature_importance = dict(zip(self.feature_names, self.model.feature_importances_))
            
            self.is_trained = True
            
            print(f"訓練完了:")
            print(f"  訓練スコア: {train_score:.3f}")
            print(f"  テストスコア: {test_score:.3f}")
            print(f"  CV平均スコア: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
            print(f"  重要な特徴量トップ5:")
            sorted_features = sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)
            for name, importance in sorted_features[:5]:
                print(f"    {name}: {importance:.3f}")
            
            return {
                'train_score': train_score,
                'test_score': test_score,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'feature_importance': self.feature_importance
            }
            
        except Exception as e:
            print(f"訓練エラー: {e}")
            return None
    
    def predict(self, features):
        """予測を実行"""
        if not self.is_trained:
            return {'error': 'モデルが訓練されていません'}
        
        try:
            # 特徴量を DataFrame に変換
            if isinstance(features, dict):
                features_df = pd.DataFrame([features])
            else:
                features_df = pd.DataFrame(features)
            
            # 特徴量の順序を合わせる
            features_df = features_df[self.feature_names]
            
            # 標準化
            features_scaled = self.scaler.transform(features_df)
            
            # 予測
            hit_probability = self.model.predict_proba(features_scaled)[0][1]
            prediction = self.model.predict(features_scaled)[0]
            
            # 信頼度計算（予測確率から）
            confidence = max(hit_probability, 1 - hit_probability)
            
            # リスク要因と成功要因を特定
            risk_factors, success_drivers = self._analyze_factors(features)
            
            return {
                'hit_probability': float(hit_probability * 100),
                'prediction': int(prediction),
                'confidence_score': float(confidence * 10),
                'risk_factors': risk_factors,
                'success_drivers': success_drivers,
                'feature_contributions': self._get_feature_contributions(features)
            }
            
        except Exception as e:
            return {'error': f'予測エラー: {e}'}
    
    def _analyze_factors(self, features):
        """リスク要因と成功要因を分析"""
        risk_factors = []
        success_drivers = []
        
        # 文化的受容性チェック
        if features.get('cultural_acceptance_score', 5) < 5:
            risk_factors.append('日本文化適合度が低い')
        elif features.get('cultural_acceptance_score', 5) > 7:
            success_drivers.append('日本文化適合度が高い')
        
        # タブーリスクチェック
        if features.get('cultural_taboo_risk', 5) > 6:
            risk_factors.append('文化的タブーリスクが高い')
        
        # 韓国での人気度チェック
        if features.get('kr_total_views', 0) < 300:
            risk_factors.append('韓国での注目度が低い')
        elif features.get('kr_total_views', 0) > 500:
            success_drivers.append('韓国で高い注目を集めている')
        
        # 日本での早期採用チェック
        if features.get('jp_youtuber_mention_count', 0) > 20:
            success_drivers.append('日本YouTuberに既に取り上げられている')
        elif features.get('jp_youtuber_mention_count', 0) < 5:
            risk_factors.append('日本での認知が限定的')
        
        # 価格アクセシビリティ
        if features.get('price_accessibility', 5) < 4:
            risk_factors.append('価格が高く一般消費者には手が届きにくい')
        elif features.get('price_accessibility', 5) > 7:
            success_drivers.append('手頃な価格設定')
        
        # 入手しやすさ
        if features.get('availability_score', 5) < 4:
            risk_factors.append('入手が困難')
        
        # 規制障壁
        if features.get('regulatory_barrier', 5) > 6:
            risk_factors.append('規制上の障壁が高い')
        
        return risk_factors[:3], success_drivers[:3]  # 最大3つずつ
    
    def _get_feature_contributions(self, features):
        """特徴量の貢献度を計算"""
        contributions = {}
        for feature_name in self.feature_names:
            value = features.get(feature_name, 0)
            importance = self.feature_importance.get(feature_name, 0)
            # 正規化された値 × 重要度で貢献度を計算
            normalized_value = min(max(value / 10.0, 0), 1)  # 0-1に正規化
            contributions[feature_name] = float(normalized_value * importance)
        return contributions
    
    def save_model(self, filepath='trained_model.pkl'):
        """訓練済みモデルを保存"""
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': self.feature_names,
                'feature_importance': self.feature_importance,
                'is_trained': self.is_trained
            }
            with open(filepath, 'wb') as f:
                pickle.dump(model_data, f)
            print(f"モデルを {filepath} に保存しました")
        except Exception as e:
            print(f"モデル保存エラー: {e}")
    
    def load_model(self, filepath='trained_model.pkl'):
        """訓練済みモデルを読み込む"""
        try:
            with open(filepath, 'rb') as f:
                model_data = pickle.load(f)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_names = model_data['feature_names']
            self.feature_importance = model_data['feature_importance']
            self.is_trained = model_data['is_trained']
            
            print(f"モデルを {filepath} から読み込みました")
        except Exception as e:
            print(f"モデル読み込みエラー: {e}")

# Flask APIの設定
app = Flask(__name__)
CORS(app)

# グローバル予測器インスタンス
predictor = HitPredictor()

@app.route('/')
def home():
    """メインページ"""
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <title>韓国→日本ヒット予測API</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .endpoint { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }
            .method { background: #007bff; color: white; padding: 3px 8px; border-radius: 3px; font-size: 12px; }
            code { background: #e9ecef; padding: 2px 5px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔮 韓国→日本ヒット予測API</h1>
            <p>美容・健康関連商品の日本市場でのヒット可能性を予測するAPIです。</p>
            
            <h2>利用可能なエンドポイント:</h2>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /predict</h3>
                <p>商品の特徴量データから日本でのヒット確率を予測</p>
                <p><strong>入力:</strong> JSON形式の特徴量データ</p>
                <p><strong>出力:</strong> ヒット確率、信頼度、リスク要因、成功要因</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">GET</span> /model_info</h3>
                <p>モデルの情報と特徴量重要度を取得</p>
            </div>
            
            <div class="endpoint">
                <h3><span class="method">POST</span> /retrain</h3>
                <p>モデルを再訓練（開発用）</p>
            </div>
            
            <h2>使用例:</h2>
            <pre><code>curl -X POST http://localhost:5000/predict \\
  -H "Content-Type: application/json" \\
  -d '{
    "kr_youtuber_mention_count": 45,
    "kr_total_views": 850,
    "cultural_acceptance_score": 9,
    "price_accessibility": 7,
    ...
  }'</code></pre>
        </div>
    </body>
    </html>
    """)

@app.route('/predict', methods=['POST'])
def predict_hit():
    """ヒット予測エンドポイント"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '入力データが必要です'}), 400
        
        result = predictor.predict(data)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/model_info', methods=['GET'])
def model_info():
    """モデル情報エンドポイント"""
    if not predictor.is_trained:
        return jsonify({'error': 'モデルが訓練されていません'}), 400
    
    return jsonify({
        'is_trained': predictor.is_trained,
        'feature_names': predictor.feature_names,
        'feature_importance': predictor.feature_importance,
        'top_features': dict(sorted(predictor.feature_importance.items(), key=lambda x: x[1], reverse=True)[:10])
    })

@app.route('/retrain', methods=['POST'])
def retrain_model():
    """モデル再訓練エンドポイント"""
    try:
        X, y, df = predictor.load_training_data()
        if X is None:
            return jsonify({'error': '訓練データの読み込みに失敗'}), 500
        
        results = predictor.train(X, y)
        if results:
            predictor.save_model()
            return jsonify({
                'message': '再訓練完了',
                'results': results
            })
        else:
            return jsonify({'error': '訓練に失敗'}), 500
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def main():
    """メイン関数"""
    print("韓国→日本ヒット予測システムを初期化中...")
    
    # 訓練データを読み込み
    X, y, df = predictor.load_training_data()
    if X is None:
        print("エラー: 訓練データの読み込みに失敗しました")
        return
    
    print(f"データセット: {len(df)} 商品, {len(predictor.feature_names)} 特徴量")
    print(f"成功事例: {sum(y)} 商品, 失敗事例: {len(y) - sum(y)} 商品")
    
    # 既存のモデルを読み込むか新規訓練
    try:
        predictor.load_model()
        print("既存のモデルを読み込みました")
    except:
        print("新規モデルを訓練中...")
        results = predictor.train(X, y)
        if results:
            predictor.save_model()
        else:
            print("エラー: モデル訓練に失敗しました")
            return
    
    print("\n=== システム準備完了 ===")
    print("APIサーバーを起動します...")
    print("ブラウザで http://localhost:5000 にアクセスしてください")
    
    # APIサーバー起動
    app.run(debug=False, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()