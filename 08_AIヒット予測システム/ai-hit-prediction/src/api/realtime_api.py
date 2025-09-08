#!/usr/bin/env python
"""
Real-time API Module
リアルタイムデータ連携とWebSocket通信
"""

from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio
import json
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.preprocessing.data_pipeline import DataPipeline
from src.preprocessing.feature_engineering import FeatureEngineer
from src.models.basic_model import HitPredictionModel
from src.multimodal.image_analyzer import MultimodalAnalyzer

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPIアプリケーション初期化
app = FastAPI(
    title="AI Hit Prediction API",
    description="リアルタイム化粧品ヒット予測API",
    version="4.0.0"
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバル変数
connected_clients = []
prediction_cache = {}
model_instance = None
pipeline_instance = None
engineer_instance = None
multimodal_instance = None


# Pydanticモデル
class ProductRequest(BaseModel):
    """製品リクエストモデル"""
    name: str = Field(..., description="製品名")
    description: str = Field(..., description="製品説明")
    keywords: List[str] = Field(..., description="キーワードリスト")
    price: int = Field(..., ge=100, le=100000, description="価格")
    brand_strength: float = Field(0.5, ge=0, le=1, description="ブランド力")
    ingredient_novelty: float = Field(0.5, ge=0, le=1, description="成分の新規性")
    market_saturation: float = Field(0.3, ge=0, le=1, description="市場飽和度")
    image_url: Optional[str] = Field(None, description="製品画像URL")


class PredictionResponse(BaseModel):
    """予測レスポンスモデル"""
    product_name: str
    hit_probability: float
    confidence: float
    risk_level: str
    factors: Dict[str, float]
    recommendations: List[str]
    timestamp: str


class MarketTrendRequest(BaseModel):
    """市場トレンドリクエストモデル"""
    category: str = Field(..., description="カテゴリ")
    period_days: int = Field(30, description="期間（日数）")
    keywords: Optional[List[str]] = Field(None, description="追跡キーワード")


class BatchPredictionRequest(BaseModel):
    """バッチ予測リクエストモデル"""
    products: List[ProductRequest]
    include_analysis: bool = Field(True, description="詳細分析を含むか")


# 初期化関数
@app.on_event("startup")
async def startup_event():
    """APIサーバー起動時の初期化"""
    global model_instance, pipeline_instance, engineer_instance, multimodal_instance
    
    logger.info("Initializing AI models and pipelines...")
    
    try:
        # モデルとパイプラインの初期化
        pipeline_instance = DataPipeline()
        engineer_instance = FeatureEngineer()
        model_instance = HitPredictionModel()
        multimodal_instance = MultimodalAnalyzer()
        
        # モデルの事前読み込み（存在する場合）
        model_path = Path("models/best_model.pkl")
        if model_path.exists():
            model_instance.load_model(str(model_path))
            logger.info("Pre-trained model loaded successfully")
        else:
            # ダミーデータで簡易学習
            logger.info("Training model with dummy data...")
            X_dummy = pd.DataFrame(np.random.rand(100, 10))
            y_dummy = np.random.choice([0, 1], 100)
            model_instance.train(X_dummy, y_dummy, validate=False)
        
        logger.info("API server initialized successfully")
        
        # バックグラウンドタスクの開始
        asyncio.create_task(market_monitoring_task())
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")


# エンドポイント
@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "AI Hit Prediction API",
        "version": "4.0.0",
        "status": "active",
        "endpoints": {
            "predict": "/api/v1/predict",
            "batch_predict": "/api/v1/batch-predict",
            "trends": "/api/v1/trends",
            "websocket": "/ws"
        }
    }


@app.post("/api/v1/predict", response_model=PredictionResponse)
async def predict_single(product: ProductRequest, background_tasks: BackgroundTasks):
    """
    単一製品のヒット予測
    
    Args:
        product: 製品情報
        background_tasks: バックグラウンドタスク
    
    Returns:
        予測結果
    """
    try:
        # キャッシュチェック
        cache_key = f"{product.name}_{product.price}_{hash(str(product.keywords))}"
        if cache_key in prediction_cache:
            cached = prediction_cache[cache_key]
            if datetime.fromisoformat(cached['timestamp']) > datetime.now() - timedelta(minutes=5):
                logger.info(f"Returning cached prediction for {product.name}")
                return PredictionResponse(**cached)
        
        # 特徴量抽出
        product_dict = product.dict()
        features = pipeline_instance.extract_features(product_dict)
        enhanced_features = engineer_instance.create_advanced_features(features)
        
        # マルチモーダル分析（画像がある場合）
        if product.image_url:
            multimodal_analysis = multimodal_instance.analyze_product(
                product.name,
                product.description,
                image_path=None,  # URLからの画像処理は簡略化
                keywords=product.keywords
            )
            
            # マルチモーダル特徴量を追加
            if 'multimodal_features' in multimodal_analysis:
                mm_features = multimodal_analysis['multimodal_features']
                enhanced_features = pd.concat([enhanced_features, mm_features], axis=1)
        
        # 予測実行
        prediction = model_instance.predict_with_confidence(enhanced_features)
        
        # 結果の構築
        hit_prob = float(prediction['hit_probability'].iloc[0])
        confidence = float(prediction['confidence'].iloc[0])
        
        # リスクレベル判定
        if hit_prob > 0.7:
            risk_level = "低"
        elif hit_prob > 0.4:
            risk_level = "中"
        else:
            risk_level = "高"
        
        # 要因分析
        factors = {
            'price_impact': np.random.uniform(0.1, 0.3),
            'brand_impact': product.brand_strength * 0.8,
            'innovation_impact': product.ingredient_novelty * 0.7,
            'market_impact': (1 - product.market_saturation) * 0.6
        }
        
        # 推奨事項生成
        recommendations = generate_recommendations(hit_prob, factors)
        
        # レスポンス作成
        response = PredictionResponse(
            product_name=product.name,
            hit_probability=hit_prob,
            confidence=confidence,
            risk_level=risk_level,
            factors=factors,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat()
        )
        
        # キャッシュ更新
        prediction_cache[cache_key] = response.dict()
        
        # WebSocketで接続クライアントに通知
        background_tasks.add_task(notify_clients, {
            "type": "new_prediction",
            "data": response.dict()
        })
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/batch-predict")
async def predict_batch(request: BatchPredictionRequest):
    """
    バッチ予測処理
    
    Args:
        request: バッチリクエスト
    
    Returns:
        バッチ予測結果
    """
    try:
        results = []
        
        for product in request.products:
            # 各製品の予測（簡略化のため単一予測を再利用）
            prediction = await predict_single(product, BackgroundTasks())
            results.append(prediction.dict())
        
        # 統計情報の追加
        hit_probs = [r['hit_probability'] for r in results]
        stats = {
            'total_products': len(results),
            'avg_hit_probability': np.mean(hit_probs),
            'high_potential_count': sum(1 for p in hit_probs if p > 0.7),
            'medium_potential_count': sum(1 for p in hit_probs if 0.4 < p <= 0.7),
            'low_potential_count': sum(1 for p in hit_probs if p <= 0.4)
        }
        
        return {
            'predictions': results,
            'statistics': stats,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/trends")
async def get_market_trends(category: str = "all", period_days: int = 30):
    """
    市場トレンド取得
    
    Args:
        category: カテゴリ
        period_days: 期間
    
    Returns:
        トレンドデータ
    """
    try:
        # モックトレンドデータ生成
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        trends = []
        categories = ['スキンケア', 'メイクアップ', 'ヘアケア'] if category == "all" else [category]
        
        for cat in categories:
            trend_values = np.cumsum(np.random.randn(len(dates)) * 2) + 50
            for date, value in zip(dates, trend_values):
                trends.append({
                    'date': date.isoformat(),
                    'category': cat,
                    'trend_score': float(max(0, value)),
                    'buzz_score': float(np.random.uniform(0.3, 0.9))
                })
        
        # トップトレンドキーワード
        keywords = get_trending_keywords()
        
        return {
            'trends': trends,
            'trending_keywords': keywords,
            'period': {
                'start': start_date.isoformat(),
                'end': end_date.isoformat(),
                'days': period_days
            }
        }
        
    except Exception as e:
        logger.error(f"Trend retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocketエンドポイント（リアルタイム通信）
    
    Args:
        websocket: WebSocket接続
    """
    await websocket.accept()
    connected_clients.append(websocket)
    
    try:
        while True:
            # クライアントからのメッセージ待機
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # メッセージタイプに応じた処理
            if message['type'] == 'subscribe':
                # トレンド購読
                await websocket.send_json({
                    "type": "subscription_confirmed",
                    "channel": message.get('channel', 'default')
                })
            
            elif message['type'] == 'ping':
                # ハートビート
                await websocket.send_json({"type": "pong"})
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        connected_clients.remove(websocket)


# ヘルパー関数
def generate_recommendations(hit_probability: float, factors: Dict[str, float]) -> List[str]:
    """
    推奨事項を生成
    
    Args:
        hit_probability: ヒット確率
        factors: 要因分析結果
    
    Returns:
        推奨事項リスト
    """
    recommendations = []
    
    if hit_probability > 0.7:
        recommendations.append("積極的な市場投入を推奨")
        recommendations.append("マーケティング予算の増額を検討")
        recommendations.append("初回生産量を増やすことを推奨")
    elif hit_probability > 0.4:
        recommendations.append("段階的な市場投入を推奨")
        recommendations.append("テストマーケティングの実施を推奨")
        recommendations.append("ターゲット層の絞り込みを検討")
    else:
        recommendations.append("製品改良の検討を推奨")
        recommendations.append("価格戦略の見直しを検討")
        recommendations.append("差別化要素の強化が必要")
    
    # 要因別の推奨
    if factors.get('price_impact', 0) < 0.2:
        recommendations.append("価格競争力の改善を検討")
    
    if factors.get('innovation_impact', 0) < 0.3:
        recommendations.append("製品の革新性を高める必要あり")
    
    return recommendations


def get_trending_keywords() -> List[Dict[str, Any]]:
    """トレンドキーワード取得"""
    keywords = [
        {"keyword": "ビタミンC", "score": 0.92, "growth": 0.15},
        {"keyword": "レチノール", "score": 0.88, "growth": 0.12},
        {"keyword": "ナイアシンアミド", "score": 0.85, "growth": 0.18},
        {"keyword": "CICA", "score": 0.82, "growth": 0.25},
        {"keyword": "CBD", "score": 0.78, "growth": 0.30}
    ]
    
    # ランダムな変動を追加
    for kw in keywords:
        kw['score'] = min(1.0, kw['score'] + np.random.uniform(-0.05, 0.05))
        kw['growth'] = kw['growth'] + np.random.uniform(-0.02, 0.02)
    
    return keywords


async def notify_clients(message: Dict):
    """
    接続中のクライアントに通知
    
    Args:
        message: 送信メッセージ
    """
    disconnected = []
    
    for client in connected_clients:
        try:
            await client.send_json(message)
        except:
            disconnected.append(client)
    
    # 切断されたクライアントを削除
    for client in disconnected:
        connected_clients.remove(client)


async def market_monitoring_task():
    """市場監視バックグラウンドタスク"""
    while True:
        try:
            # 5分ごとに市場データを更新
            await asyncio.sleep(300)
            
            # トレンドデータの更新（実際にはAPIから取得）
            trend_update = {
                "type": "trend_update",
                "data": {
                    "keywords": get_trending_keywords(),
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # 全クライアントに通知
            await notify_clients(trend_update)
            
            logger.info("Market data updated and broadcasted")
            
        except Exception as e:
            logger.error(f"Market monitoring error: {e}")


# エラーハンドラ
@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """一般的な例外ハンドラ"""
    logger.error(f"Unhandled exception: {exc}")
    return HTTPException(status_code=500, detail="Internal server error")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)