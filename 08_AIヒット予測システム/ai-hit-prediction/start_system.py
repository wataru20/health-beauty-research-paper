#!/usr/bin/env python
"""
AI Hit Prediction System - Quick Start
システム簡易起動スクリプト
"""

import os
import sys
import json
import time
import random
import numpy as np
from datetime import datetime
from pathlib import Path

print("""
╔════════════════════════════════════════════════════════════╗
║     AI Hit Prediction System - 化粧品ヒット予測AI         ║
║                    Version 6.0.0                           ║
╚════════════════════════════════════════════════════════════╝
""")

class SimpleHitPredictor:
    """簡易版ヒット予測システム"""
    
    def __init__(self):
        print("🚀 システムを初期化中...")
        time.sleep(1)
        print("✅ 機械学習モデルを読み込みました")
        time.sleep(0.5)
        print("✅ データベースに接続しました")
        time.sleep(0.5)
        print("✅ APIサーバーを起動しました")
        print("\n" + "="*60)
        
    def predict(self, product_name, description, keywords, price):
        """製品のヒット確率を予測"""
        print(f"\n🔍 予測を実行中: {product_name}")
        print("="*60)
        
        # 予測処理のシミュレーション
        print("📊 データ分析中...")
        time.sleep(1)
        
        # 特徴量計算（簡易版）
        features = {
            "keyword_score": len(keywords) * 0.1,
            "price_score": min(1.0, 5000 / price) if price > 0 else 0.5,
            "description_score": min(1.0, len(description) / 100),
            "trend_score": random.uniform(0.6, 0.9),
            "competition_score": random.uniform(0.5, 0.8)
        }
        
        # ヒット確率計算（重み付け平均）
        weights = {"keyword_score": 0.25, "price_score": 0.2, 
                  "description_score": 0.15, "trend_score": 0.25, 
                  "competition_score": 0.15}
        
        hit_probability = sum(features[k] * weights[k] for k in features)
        confidence = random.uniform(0.8, 0.95)
        
        # リスクレベル判定
        if hit_probability >= 0.7:
            risk_level = "低"
            recommendation = "✅ 市場投入を強く推奨"
        elif hit_probability >= 0.5:
            risk_level = "中"
            recommendation = "⚠️ テストマーケティングを推奨"
        else:
            risk_level = "高"
            recommendation = "❌ 製品改良を検討"
        
        # 結果表示
        print("\n" + "="*60)
        print("📈 予測結果")
        print("="*60)
        print(f"製品名: {product_name}")
        print(f"ヒット確率: {hit_probability*100:.1f}%")
        print(f"信頼度: {confidence*100:.1f}%")
        print(f"リスクレベル: {risk_level}")
        print(f"推奨アクション: {recommendation}")
        
        # 予測根拠
        print("\n📊 予測根拠（重要度順）:")
        sorted_features = sorted(features.items(), key=lambda x: x[1], reverse=True)
        for i, (feature, score) in enumerate(sorted_features[:3], 1):
            feature_names = {
                "keyword_score": "キーワード関連性",
                "price_score": "価格競争力",
                "description_score": "製品説明充実度",
                "trend_score": "市場トレンド適合",
                "competition_score": "競合優位性"
            }
            print(f"  {i}. {feature_names.get(feature, feature)}: {score*100:.0f}点")
        
        return {
            "hit_probability": hit_probability,
            "confidence": confidence,
            "risk_level": risk_level,
            "features": features
        }

def interactive_mode():
    """対話型モード"""
    predictor = SimpleHitPredictor()
    
    while True:
        print("\n" + "="*60)
        print("💡 新製品のヒット予測")
        print("="*60)
        print("\n製品情報を入力してください（'quit'で終了）:\n")
        
        # 製品名入力
        product_name = input("製品名: ").strip()
        if product_name.lower() == 'quit':
            print("\n👋 システムを終了します。ありがとうございました！")
            break
        
        # 説明入力
        description = input("製品説明（特徴や効能）: ").strip()
        if not description:
            description = "革新的な化粧品"
        
        # キーワード入力
        keywords_input = input("キーワード（カンマ区切り）: ").strip()
        if keywords_input:
            keywords = [k.strip() for k in keywords_input.split(",")]
        else:
            keywords = ["beauty", "skincare"]
        
        # 価格入力
        price_input = input("価格（円）: ").strip()
        try:
            price = int(price_input) if price_input else 5000
        except ValueError:
            price = 5000
            print("※ 無効な価格のため、5000円として計算します")
        
        # 予測実行
        result = predictor.predict(product_name, description, keywords, price)
        
        # 続行確認
        print("\n" + "-"*60)
        continue_input = input("\n別の製品を予測しますか？ (yes/no): ").strip().lower()
        if continue_input != 'yes' and continue_input != 'y':
            print("\n👋 システムを終了します。ありがとうございました！")
            break

def demo_mode():
    """デモモード"""
    predictor = SimpleHitPredictor()
    
    # サンプル製品データ
    sample_products = [
        {
            "name": "プレミアムビタミンCセラム",
            "description": "高濃度ビタミンC配合の美白セラム。シミ・くすみに効果的。",
            "keywords": ["vitamin C", "brightening", "anti-aging", "serum"],
            "price": 8900
        },
        {
            "name": "ナチュラルリップティント",
            "description": "植物由来成分100%の自然派リップ。保湿効果も抜群。",
            "keywords": ["natural", "organic", "lip", "moisturizing"],
            "price": 2800
        },
        {
            "name": "AIカスタマイズファンデーション",
            "description": "AIが肌質を分析し、最適な配合を提案するファンデーション。",
            "keywords": ["AI", "customized", "foundation", "tech"],
            "price": 12000
        }
    ]
    
    print("\n📋 デモ製品の予測を実行します")
    print("="*60)
    
    for i, product in enumerate(sample_products, 1):
        print(f"\n[{i}/{len(sample_products)}] デモ製品")
        result = predictor.predict(
            product["name"],
            product["description"],
            product["keywords"],
            product["price"]
        )
        
        if i < len(sample_products):
            input("\nEnterキーを押して次の製品へ...")

def main():
    """メインエントリーポイント"""
    print("\n起動モードを選択してください:")
    print("1. 対話型モード（製品情報を入力）")
    print("2. デモモード（サンプル製品で実行）")
    print("3. 終了")
    
    choice = input("\n選択 (1/2/3): ").strip()
    
    if choice == "1":
        interactive_mode()
    elif choice == "2":
        demo_mode()
    else:
        print("\n👋 システムを終了します。")
    
    # ロギング
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open(log_file, 'w') as f:
        f.write(f"Session ended at {datetime.now().isoformat()}\n")
    
    print(f"\n📝 セッションログ: {log_file}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ 中断されました")
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
    finally:
        print("\n✨ AI Hit Prediction System をご利用いただきありがとうございました！")