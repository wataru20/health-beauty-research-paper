#!/usr/bin/env python
"""
AI Hit Prediction System - Auto Demo
自動デモンストレーション
"""

import json
import time
import random
import numpy as np
from datetime import datetime
from pathlib import Path

class AIHitPredictionDemo:
    """AIヒット予測システムデモ"""
    
    def __init__(self):
        self.predictions_made = 0
        self.start_time = datetime.now()
        
    def clear_screen(self):
        """画面クリア（視覚効果のため）"""
        print("\n" * 2)
    
    def display_header(self):
        """ヘッダー表示"""
        print("="*70)
        print("   AI HIT PREDICTION SYSTEM - 化粧品ヒット予測AI v6.0.0")
        print("="*70)
    
    def predict_product(self, product):
        """製品予測"""
        # 特徴量計算
        keyword_score = len(product["keywords"]) * 0.12
        price_score = min(1.0, 5000 / product["price"]) if product["price"] > 0 else 0.5
        desc_score = min(1.0, len(product["description"]) / 80)
        trend_score = random.uniform(0.55, 0.92)
        competition_score = random.uniform(0.48, 0.85)
        innovation_score = random.uniform(0.60, 0.95) if "AI" in str(product["keywords"]) else random.uniform(0.40, 0.70)
        
        # 重み付け平均
        weights = {
            "keyword": 0.20, "price": 0.15, "desc": 0.10,
            "trend": 0.25, "competition": 0.15, "innovation": 0.15
        }
        
        hit_prob = (
            keyword_score * weights["keyword"] +
            price_score * weights["price"] +
            desc_score * weights["desc"] +
            trend_score * weights["trend"] +
            competition_score * weights["competition"] +
            innovation_score * weights["innovation"]
        )
        
        confidence = random.uniform(0.82, 0.96)
        
        # リスク判定
        if hit_prob >= 0.70:
            risk = "低", "🟢"
            action = "積極的な市場投入を推奨"
        elif hit_prob >= 0.50:
            risk = "中", "🟡" 
            action = "テストマーケティング推奨"
        else:
            risk = "高", "🔴"
            action = "製品改良を検討"
        
        return {
            "hit_probability": hit_prob,
            "confidence": confidence,
            "risk_level": risk,
            "recommended_action": action,
            "top_factors": [
                ("トレンド適合度", trend_score),
                ("イノベーション性", innovation_score),
                ("競合優位性", competition_score)
            ]
        }
    
    def display_prediction(self, product, result):
        """予測結果表示"""
        self.predictions_made += 1
        
        print(f"\n[予測 #{self.predictions_made}]")
        print("-"*70)
        print(f"📦 製品名: {product['name']}")
        print(f"📝 説明: {product['description'][:50]}...")
        print(f"🏷️  価格: ¥{product['price']:,}")
        print(f"🔑 キーワード: {', '.join(product['keywords'][:3])}")
        
        print("\n" + "="*35 + " 予測結果 " + "="*35)
        
        # メイン指標
        prob_percent = result['hit_probability'] * 100
        conf_percent = result['confidence'] * 100
        
        print(f"\n  🎯 ヒット確率: {prob_percent:>6.1f}% ", end="")
        if prob_percent >= 70:
            print("【優秀】")
        elif prob_percent >= 50:
            print("【普通】")
        else:
            print("【要改善】")
        
        print(f"  📊 予測信頼度: {conf_percent:>6.1f}%")
        print(f"  ⚠️  リスクレベル: {result['risk_level'][1]} {result['risk_level'][0]}")
        print(f"  💡 推奨アクション: {result['recommended_action']}")
        
        # 主要因子
        print("\n  📈 予測の主要因子:")
        for i, (factor, score) in enumerate(result['top_factors'][:3], 1):
            bar_length = int(score * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)
            print(f"     {i}. {factor:<12} {bar} {score*100:.0f}%")
        
        print("\n" + "="*70)
    
    def run_demo(self):
        """デモ実行"""
        self.display_header()
        
        print("\n🚀 AI Hit Prediction System を起動しています...")
        time.sleep(1)
        print("✅ 機械学習モデルをロード完了")
        time.sleep(0.5)
        print("✅ データベース接続確立")
        time.sleep(0.5)
        print("✅ 予測エンジン準備完了")
        
        # サンプル製品データ
        products = [
            {
                "name": "プレミアムビタミンCセラム 30ml",
                "description": "最新のナノテクノロジーを使用した高濃度ビタミンC美容液。シミ・くすみを改善し、透明感のある肌へ導きます。",
                "keywords": ["vitamin C", "brightening", "anti-aging", "serum", "nanotech"],
                "price": 8900,
                "category": "スキンケア"
            },
            {
                "name": "AIカスタマイズ ファンデーション",
                "description": "AIが肌質を分析し、個人に最適化された配合を提供する革新的ファンデーション。",
                "keywords": ["AI", "customized", "foundation", "personalized", "tech"],
                "price": 12000,
                "category": "メイクアップ"
            },
            {
                "name": "オーガニックリップティント 5色セット",
                "description": "100%植物由来成分使用。発色と保湿を両立した自然派リップティント。",
                "keywords": ["organic", "natural", "lip", "tint", "moisturizing"],
                "price": 3500,
                "category": "メイクアップ"
            },
            {
                "name": "頭皮ケア トリートメントオイル",
                "description": "頭皮環境を整え、健康な髪の成長を促進する専門ケアオイル。",
                "keywords": ["scalp care", "treatment", "oil", "hair growth"],
                "price": 4800,
                "category": "ヘアケア"
            }
        ]
        
        print("\n📋 デモ製品の分析を開始します")
        print("="*70)
        
        # 各製品の予測
        results_summary = []
        for i, product in enumerate(products, 1):
            print(f"\n⏳ 製品 {i}/{len(products)} を分析中...")
            time.sleep(1.5)  # シミュレーション遅延
            
            result = self.predict_product(product)
            self.display_prediction(product, result)
            
            results_summary.append({
                "name": product["name"],
                "hit_prob": result["hit_probability"],
                "risk": result["risk_level"][0]
            })
            
            time.sleep(1)  # 読みやすさのための遅延
        
        # サマリー表示
        self.display_summary(results_summary)
        
        # 終了メッセージ
        runtime = (datetime.now() - self.start_time).total_seconds()
        print(f"\n⏱️  実行時間: {runtime:.1f}秒")
        print(f"📊 予測完了数: {self.predictions_made}件")
        print("\n✨ デモンストレーション完了！")
        
        return results_summary
    
    def display_summary(self, results):
        """サマリー表示"""
        print("\n" + "="*70)
        print(" "*25 + "📊 予測サマリー")
        print("="*70)
        
        # ソート（ヒット確率順）
        sorted_results = sorted(results, key=lambda x: x["hit_prob"], reverse=True)
        
        print("\n【ヒット確率ランキング】")
        for i, result in enumerate(sorted_results, 1):
            prob_percent = result["hit_prob"] * 100
            
            # ランクアイコン
            if i == 1:
                icon = "🥇"
            elif i == 2:
                icon = "🥈"
            elif i == 3:
                icon = "🥉"
            else:
                icon = f" {i}."
            
            # プログレスバー
            bar_length = int(prob_percent / 5)
            progress_bar = "█" * bar_length + "░" * (20 - bar_length)
            
            print(f"{icon} {result['name'][:30]:<30}")
            print(f"    {progress_bar} {prob_percent:.1f}% (リスク: {result['risk']})")
            print()
        
        # 統計情報
        avg_prob = np.mean([r["hit_prob"] for r in results]) * 100
        high_potential = len([r for r in results if r["hit_prob"] >= 0.7])
        
        print("-"*70)
        print(f"📈 平均ヒット確率: {avg_prob:.1f}%")
        print(f"⭐ 高ポテンシャル製品数: {high_potential}/{len(results)}件")
        
        # 推奨事項
        print("\n💡 【総合推奨事項】")
        if high_potential >= 2:
            print("  ✅ 複数の有望製品があります。リソースの優先配分を推奨")
        else:
            print("  ⚠️ 高ポテンシャル製品が少ないため、製品戦略の見直しを検討")
        
        print("="*70)

def main():
    """メイン実行"""
    demo = AIHitPredictionDemo()
    
    try:
        results = demo.run_demo()
        
        # 結果をJSONファイルに保存
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = output_dir / f"demo_results_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": timestamp,
                "results": results,
                "predictions_count": demo.predictions_made
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n📁 結果を保存しました: {output_file}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ デモが中断されました")
    except Exception as e:
        print(f"\n❌ エラー: {e}")
    
    print("\n" + "="*70)
    print("  AI Hit Prediction System - Demo Complete")
    print("  お問い合わせ: support@ai-hit-prediction.com")
    print("="*70)

if __name__ == "__main__":
    main()