#!/usr/bin/env python
"""
Multimodal Image Analysis Module
製品画像からの特徴抽出とトレンド分析
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from PIL import Image
import io
import base64
import logging
from pathlib import Path
import json
from datetime import datetime

# 画像処理とML
try:
    import torch
    import torchvision.transforms as transforms
    from transformers import (
        CLIPProcessor, 
        CLIPModel,
        BlipProcessor,
        BlipForConditionalGeneration
    )
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("Transformers library not available. Using mock implementation.")

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageAnalyzer:
    """画像分析クラス"""
    
    def __init__(self, model_type: str = 'clip'):
        """
        初期化
        
        Args:
            model_type: 使用するモデルタイプ ('clip', 'blip', 'mock')
        """
        self.model_type = model_type if TRANSFORMERS_AVAILABLE else 'mock'
        self.model = None
        self.processor = None
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu' if TRANSFORMERS_AVAILABLE else 'mock'
        
        self._initialize_model()
    
    def _initialize_model(self):
        """モデルの初期化"""
        if self.model_type == 'clip' and TRANSFORMERS_AVAILABLE:
            try:
                self.processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
                self.model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
                if self.device != 'mock':
                    self.model.to(self.device)
                logger.info("CLIP model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load CLIP model: {e}. Using mock mode.")
                self.model_type = 'mock'
        
        elif self.model_type == 'blip' and TRANSFORMERS_AVAILABLE:
            try:
                self.processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
                self.model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
                if self.device != 'mock':
                    self.model.to(self.device)
                logger.info("BLIP model loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load BLIP model: {e}. Using mock mode.")
                self.model_type = 'mock'
        
        else:
            self.model_type = 'mock'
            logger.info("Using mock image analysis mode")
    
    def analyze_product_image(self, image_path: str) -> Dict[str, Any]:
        """
        製品画像を分析
        
        Args:
            image_path: 画像ファイルパス
        
        Returns:
            分析結果
        """
        try:
            # 画像を読み込み
            image = Image.open(image_path).convert('RGB')
            
            # 分析実行
            if self.model_type == 'clip':
                return self._analyze_with_clip(image)
            elif self.model_type == 'blip':
                return self._analyze_with_blip(image)
            else:
                return self._analyze_mock(image)
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            return self._get_default_analysis()
    
    def _analyze_with_clip(self, image: Image.Image) -> Dict[str, Any]:
        """CLIPモデルで分析"""
        # テキストプロンプト（化粧品の特徴）
        text_prompts = [
            "luxury cosmetic product",
            "natural organic beauty product",
            "scientific advanced formula",
            "youthful fresh design",
            "premium packaging",
            "minimalist design",
            "colorful vibrant packaging",
            "eco-friendly sustainable"
        ]
        
        # 画像とテキストを処理
        inputs = self.processor(
            text=text_prompts,
            images=image,
            return_tensors="pt",
            padding=True
        )
        
        if self.device != 'mock':
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # 推論実行
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)
        
        # スコアを抽出
        scores = probs[0].cpu().numpy()
        
        # 結果をまとめる
        features = {}
        for prompt, score in zip(text_prompts, scores):
            feature_name = prompt.replace(" ", "_")
            features[feature_name] = float(score)
        
        # 追加の分析
        return {
            'visual_features': features,
            'luxury_score': float(features.get('luxury_cosmetic_product', 0)),
            'sustainability_score': float(features.get('eco-friendly_sustainable', 0)),
            'innovation_score': float(features.get('scientific_advanced_formula', 0)),
            'design_quality': float(np.mean([
                features.get('premium_packaging', 0),
                features.get('minimalist_design', 0)
            ])),
            'target_demographic': self._infer_demographic(features),
            'color_palette': self._extract_color_palette(image),
            'packaging_type': self._classify_packaging(image)
        }
    
    def _analyze_with_blip(self, image: Image.Image) -> Dict[str, Any]:
        """BLIPモデルで分析"""
        # 画像キャプション生成
        inputs = self.processor(image, return_tensors="pt")
        
        if self.device != 'mock':
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # キャプション生成
        with torch.no_grad():
            out = self.model.generate(**inputs, max_length=50)
            caption = self.processor.decode(out[0], skip_special_tokens=True)
        
        # キャプションから特徴を抽出
        features = self._extract_features_from_caption(caption)
        
        return {
            'caption': caption,
            'visual_features': features,
            'luxury_score': features.get('luxury', 0.5),
            'sustainability_score': features.get('eco', 0.3),
            'innovation_score': features.get('innovative', 0.4),
            'design_quality': features.get('design', 0.6),
            'target_demographic': self._infer_demographic(features),
            'color_palette': self._extract_color_palette(image),
            'packaging_type': self._classify_packaging(image)
        }
    
    def _analyze_mock(self, image: Image.Image) -> Dict[str, Any]:
        """モック分析（APIなしでも動作）"""
        # ランダムな分析結果を生成
        np.random.seed(hash(str(image.size)) % 2**32)
        
        return {
            'visual_features': {
                'luxury_cosmetic_product': np.random.uniform(0.3, 0.9),
                'natural_organic_beauty_product': np.random.uniform(0.2, 0.8),
                'scientific_advanced_formula': np.random.uniform(0.4, 0.9),
                'youthful_fresh_design': np.random.uniform(0.3, 0.7),
                'premium_packaging': np.random.uniform(0.4, 0.95),
                'minimalist_design': np.random.uniform(0.2, 0.8),
                'colorful_vibrant_packaging': np.random.uniform(0.1, 0.7),
                'eco-friendly_sustainable': np.random.uniform(0.2, 0.6)
            },
            'luxury_score': np.random.uniform(0.4, 0.9),
            'sustainability_score': np.random.uniform(0.2, 0.7),
            'innovation_score': np.random.uniform(0.3, 0.8),
            'design_quality': np.random.uniform(0.5, 0.9),
            'target_demographic': np.random.choice(['Gen Z', 'Millennial', 'Gen X', 'All Ages']),
            'color_palette': self._extract_color_palette(image),
            'packaging_type': np.random.choice(['Bottle', 'Jar', 'Tube', 'Compact', 'Spray'])
        }
    
    def _extract_features_from_caption(self, caption: str) -> Dict[str, float]:
        """キャプションから特徴を抽出"""
        keywords = {
            'luxury': ['luxury', 'premium', 'elegant', 'sophisticated'],
            'eco': ['eco', 'natural', 'organic', 'sustainable'],
            'innovative': ['innovative', 'advanced', 'scientific', 'technology'],
            'design': ['beautiful', 'sleek', 'modern', 'stylish']
        }
        
        caption_lower = caption.lower()
        features = {}
        
        for feature, words in keywords.items():
            score = sum(1 for word in words if word in caption_lower)
            features[feature] = min(1.0, score * 0.3)
        
        return features
    
    def _infer_demographic(self, features: Dict) -> str:
        """ターゲット層を推定"""
        if features.get('youthful_fresh_design', 0) > 0.6:
            return 'Gen Z'
        elif features.get('minimalist_design', 0) > 0.7:
            return 'Millennial'
        elif features.get('luxury_cosmetic_product', 0) > 0.8:
            return 'Premium Segment'
        else:
            return 'Mass Market'
    
    def _extract_color_palette(self, image: Image.Image) -> Dict[str, Any]:
        """色パレットを抽出"""
        # 画像をリサイズして計算を高速化
        image_small = image.resize((150, 150))
        pixels = np.array(image_small)
        
        # 主要な色を抽出（簡易版）
        avg_color = pixels.mean(axis=(0, 1))
        
        # 色の特徴を分析
        r, g, b = avg_color
        
        # 色温度（暖色/寒色）
        warmth = (r - b) / 255.0
        
        # 彩度
        saturation = (max(r, g, b) - min(r, g, b)) / 255.0
        
        # 明度
        brightness = max(r, g, b) / 255.0
        
        return {
            'dominant_color': f"rgb({int(r)},{int(g)},{int(b)})",
            'warmth_score': float(warmth),
            'saturation': float(saturation),
            'brightness': float(brightness),
            'color_category': self._categorize_color(r, g, b)
        }
    
    def _categorize_color(self, r: float, g: float, b: float) -> str:
        """色をカテゴライズ"""
        if max(r, g, b) - min(r, g, b) < 30:
            return 'Neutral'
        elif r > g and r > b:
            return 'Warm'
        elif b > r and b > g:
            return 'Cool'
        elif g > r and g > b:
            return 'Fresh'
        else:
            return 'Balanced'
    
    def _classify_packaging(self, image: Image.Image) -> str:
        """パッケージタイプを分類"""
        # 簡易的なアスペクト比ベースの分類
        width, height = image.size
        aspect_ratio = width / height
        
        if aspect_ratio > 1.5:
            return 'Box'
        elif aspect_ratio < 0.7:
            return 'Bottle'
        elif 0.9 < aspect_ratio < 1.1:
            return 'Jar'
        else:
            return 'Tube'
    
    def _get_default_analysis(self) -> Dict[str, Any]:
        """デフォルトの分析結果"""
        return {
            'visual_features': {},
            'luxury_score': 0.5,
            'sustainability_score': 0.5,
            'innovation_score': 0.5,
            'design_quality': 0.5,
            'target_demographic': 'Unknown',
            'color_palette': {
                'dominant_color': 'rgb(128,128,128)',
                'warmth_score': 0.0,
                'saturation': 0.0,
                'brightness': 0.5,
                'color_category': 'Neutral'
            },
            'packaging_type': 'Unknown'
        }
    
    def batch_analyze(self, image_paths: List[str]) -> pd.DataFrame:
        """
        複数画像のバッチ分析
        
        Args:
            image_paths: 画像パスのリスト
        
        Returns:
            分析結果のDataFrame
        """
        results = []
        
        for i, path in enumerate(image_paths):
            logger.info(f"Analyzing image {i+1}/{len(image_paths)}: {path}")
            
            analysis = self.analyze_product_image(path)
            analysis['image_path'] = path
            analysis['analysis_timestamp'] = datetime.now().isoformat()
            
            results.append(analysis)
        
        # DataFrameに変換
        df = pd.DataFrame(results)
        
        # スコアの正規化
        score_columns = ['luxury_score', 'sustainability_score', 'innovation_score', 'design_quality']
        for col in score_columns:
            if col in df.columns:
                df[col] = df[col].clip(0, 1)
        
        return df
    
    def generate_visual_insights(self, analysis_df: pd.DataFrame) -> Dict[str, Any]:
        """
        視覚的インサイトを生成
        
        Args:
            analysis_df: 分析結果のDataFrame
        
        Returns:
            インサイト
        """
        insights = {
            'total_analyzed': len(analysis_df),
            'avg_luxury_score': analysis_df['luxury_score'].mean(),
            'avg_sustainability_score': analysis_df['sustainability_score'].mean(),
            'avg_innovation_score': analysis_df['innovation_score'].mean(),
            'avg_design_quality': analysis_df['design_quality'].mean(),
            'dominant_demographic': analysis_df['target_demographic'].mode().iloc[0] if not analysis_df.empty else 'Unknown',
            'common_packaging': analysis_df['packaging_type'].mode().iloc[0] if not analysis_df.empty else 'Unknown',
            'trend_indicators': {
                'minimalist_trend': (analysis_df['design_quality'] > 0.7).mean(),
                'eco_trend': (analysis_df['sustainability_score'] > 0.6).mean(),
                'premium_trend': (analysis_df['luxury_score'] > 0.7).mean()
            }
        }
        
        return insights


class MultimodalAnalyzer:
    """マルチモーダル統合分析クラス"""
    
    def __init__(self):
        """初期化"""
        self.image_analyzer = ImageAnalyzer()
        self.text_features = {}
        self.combined_features = {}
    
    def analyze_product(self, 
                       product_name: str,
                       description: str,
                       image_path: Optional[str] = None,
                       keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        製品の総合的な分析
        
        Args:
            product_name: 製品名
            description: 製品説明
            image_path: 画像パス（オプション）
            keywords: キーワードリスト（オプション）
        
        Returns:
            統合分析結果
        """
        results = {
            'product_name': product_name,
            'timestamp': datetime.now().isoformat()
        }
        
        # テキスト分析
        text_analysis = self._analyze_text(product_name, description, keywords)
        results['text_analysis'] = text_analysis
        
        # 画像分析
        if image_path and Path(image_path).exists():
            image_analysis = self.image_analyzer.analyze_product_image(image_path)
            results['image_analysis'] = image_analysis
            
            # マルチモーダル統合スコア
            results['integrated_scores'] = self._integrate_scores(text_analysis, image_analysis)
        else:
            results['image_analysis'] = None
            results['integrated_scores'] = text_analysis.get('scores', {})
        
        # ヒット予測への寄与度計算
        results['multimodal_features'] = self._create_multimodal_features(results)
        
        return results
    
    def _analyze_text(self, product_name: str, description: str, 
                     keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """テキスト分析"""
        # キーワード分析
        desc_lower = description.lower()
        
        trend_keywords = {
            'innovation': ['innovative', 'breakthrough', 'advanced', 'cutting-edge', 'revolutionary'],
            'natural': ['natural', 'organic', 'botanical', 'plant-based', 'eco'],
            'science': ['clinical', 'tested', 'proven', 'dermatologist', 'formula'],
            'luxury': ['premium', 'luxury', 'exclusive', 'prestige', 'haute']
        }
        
        scores = {}
        for category, words in trend_keywords.items():
            score = sum(1 for word in words if word in desc_lower) / len(words)
            scores[category] = min(1.0, score)
        
        # 感情分析（簡易版）
        positive_words = ['amazing', 'perfect', 'excellent', 'best', 'wonderful']
        negative_words = ['bad', 'poor', 'worst', 'terrible', 'awful']
        
        sentiment = (sum(1 for w in positive_words if w in desc_lower) - 
                    sum(1 for w in negative_words if w in desc_lower))
        sentiment_score = (sentiment + 5) / 10  # -5~5を0~1に正規化
        
        return {
            'scores': scores,
            'sentiment': sentiment_score,
            'description_length': len(description),
            'keyword_density': len(keywords) / len(description.split()) if keywords else 0
        }
    
    def _integrate_scores(self, text_analysis: Dict, image_analysis: Dict) -> Dict[str, float]:
        """スコアの統合"""
        integrated = {}
        
        # テキストと画像のスコアを重み付け平均
        text_weight = 0.4
        image_weight = 0.6
        
        # 共通スコアの統合
        if 'scores' in text_analysis and image_analysis:
            integrated['innovation_score'] = (
                text_analysis['scores'].get('innovation', 0.5) * text_weight +
                image_analysis.get('innovation_score', 0.5) * image_weight
            )
            integrated['luxury_score'] = (
                text_analysis['scores'].get('luxury', 0.5) * text_weight +
                image_analysis.get('luxury_score', 0.5) * image_weight
            )
            integrated['sustainability_score'] = (
                text_analysis['scores'].get('natural', 0.5) * text_weight +
                image_analysis.get('sustainability_score', 0.5) * image_weight
            )
            
            # 総合品質スコア
            integrated['overall_quality'] = np.mean([
                integrated['innovation_score'],
                integrated['luxury_score'],
                image_analysis.get('design_quality', 0.5)
            ])
        
        return integrated
    
    def _create_multimodal_features(self, analysis: Dict) -> pd.DataFrame:
        """マルチモーダル特徴量を作成"""
        features = {}
        
        # テキスト特徴
        if analysis.get('text_analysis'):
            text = analysis['text_analysis']
            features['text_sentiment'] = text.get('sentiment', 0.5)
            features['text_innovation'] = text.get('scores', {}).get('innovation', 0.5)
            features['text_natural'] = text.get('scores', {}).get('natural', 0.5)
            features['text_science'] = text.get('scores', {}).get('science', 0.5)
            features['text_luxury'] = text.get('scores', {}).get('luxury', 0.5)
        
        # 画像特徴
        if analysis.get('image_analysis'):
            img = analysis['image_analysis']
            features['img_luxury'] = img.get('luxury_score', 0.5)
            features['img_sustainability'] = img.get('sustainability_score', 0.5)
            features['img_innovation'] = img.get('innovation_score', 0.5)
            features['img_design_quality'] = img.get('design_quality', 0.5)
            
            # 色特徴
            if 'color_palette' in img:
                features['color_warmth'] = img['color_palette'].get('warmth_score', 0)
                features['color_saturation'] = img['color_palette'].get('saturation', 0.5)
                features['color_brightness'] = img['color_palette'].get('brightness', 0.5)
        
        # 統合スコア
        if analysis.get('integrated_scores'):
            for key, value in analysis['integrated_scores'].items():
                features[f'integrated_{key}'] = value
        
        # 交差特徴量
        if 'text_luxury' in features and 'img_luxury' in features:
            features['luxury_consistency'] = 1 - abs(features['text_luxury'] - features['img_luxury'])
        
        if 'text_innovation' in features and 'img_innovation' in features:
            features['innovation_consistency'] = 1 - abs(features['text_innovation'] - features['img_innovation'])
        
        return pd.DataFrame([features])