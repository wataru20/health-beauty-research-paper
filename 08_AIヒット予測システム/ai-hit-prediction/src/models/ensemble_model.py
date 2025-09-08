#!/usr/bin/env python
"""
Ensemble Learning Module
アンサンブル学習による予測精度向上
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    VotingClassifier,
    StackingClassifier
)
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import (
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score,
    roc_auc_score,
    confusion_matrix
)

# XGBoostとLightGBMのインポート（オプショナル）
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logging.warning("XGBoost not available. Using alternative models.")

try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    logging.warning("LightGBM not available. Using alternative models.")

import joblib
import logging
from datetime import datetime

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnsembleModel:
    """アンサンブルモデルクラス"""
    
    def __init__(self, ensemble_type: str = 'voting'):
        """
        初期化
        
        Args:
            ensemble_type: アンサンブルタイプ ('voting', 'stacking', 'blending', 'advanced')
        """
        self.ensemble_type = ensemble_type
        self.base_models = {}
        self.ensemble_model = None
        self.model_weights = None
        self.feature_importance = None
        self.performance_metrics = {}
        
        self._initialize_base_models()
    
    def _initialize_base_models(self):
        """ベースモデルの初期化"""
        
        # Random Forest
        self.base_models['rf'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            max_features='sqrt',
            random_state=42,
            n_jobs=-1
        )
        
        # XGBoost（利用可能な場合）
        if XGBOOST_AVAILABLE:
            self.base_models['xgb'] = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=8,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                gamma=0.1,
                reg_alpha=0.1,
                reg_lambda=1,
                objective='binary:logistic',
                random_state=42,
                n_jobs=-1
            )
        
        # LightGBM（利用可能な場合）
        if LIGHTGBM_AVAILABLE:
            self.base_models['lgb'] = lgb.LGBMClassifier(
                n_estimators=200,
                num_leaves=50,
                max_depth=8,
                learning_rate=0.1,
                feature_fraction=0.8,
                bagging_fraction=0.8,
                bagging_freq=5,
                lambda_l1=0.1,
                lambda_l2=0.1,
                min_child_samples=20,
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )
        
        # Gradient Boosting
        self.base_models['gb'] = GradientBoostingClassifier(
            n_estimators=150,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42
        )
        
        logger.info(f"Initialized {len(self.base_models)} base models")
    
    def train(self, X_train: pd.DataFrame, y_train: np.ndarray,
             X_val: Optional[pd.DataFrame] = None, 
             y_val: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        アンサンブルモデルの学習
        
        Args:
            X_train: 訓練データの特徴量
            y_train: 訓練データのターゲット
            X_val: 検証データの特徴量
            y_val: 検証データのターゲット
        
        Returns:
            学習結果
        """
        logger.info(f"Training ensemble model with {self.ensemble_type} method")
        
        if self.ensemble_type == 'voting':
            return self._train_voting_ensemble(X_train, y_train, X_val, y_val)
        elif self.ensemble_type == 'stacking':
            return self._train_stacking_ensemble(X_train, y_train, X_val, y_val)
        elif self.ensemble_type == 'blending':
            return self._train_blending_ensemble(X_train, y_train, X_val, y_val)
        elif self.ensemble_type == 'advanced':
            return self._train_advanced_ensemble(X_train, y_train, X_val, y_val)
        else:
            raise ValueError(f"Unknown ensemble type: {self.ensemble_type}")
    
    def _train_voting_ensemble(self, X_train: pd.DataFrame, y_train: np.ndarray,
                              X_val: Optional[pd.DataFrame] = None,
                              y_val: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Voting Ensembleの学習"""
        
        # 個別モデルの学習と評価
        model_performances = {}
        
        for name, model in self.base_models.items():
            logger.info(f"Training {name}...")
            
            # 学習
            model.fit(X_train, y_train)
            
            # クロスバリデーション評価
            cv_scores = cross_val_score(
                model, X_train, y_train,
                cv=5, scoring='f1', n_jobs=-1
            )
            
            model_performances[name] = {
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }
            
            # 検証データでの評価
            if X_val is not None and y_val is not None:
                val_pred = model.predict(X_val)
                model_performances[name]['val_f1'] = f1_score(y_val, val_pred)
        
        # パフォーマンスに基づく重み付け
        if X_val is not None and y_val is not None:
            weights = [model_performances[name]['val_f1'] for name in self.base_models.keys()]
        else:
            weights = [model_performances[name]['cv_mean'] for name in self.base_models.keys()]
        
        # 重みの正規化
        weights = np.array(weights)
        weights = weights / weights.sum()
        self.model_weights = dict(zip(self.base_models.keys(), weights))
        
        # Voting Classifierの作成
        estimators = [(name, model) for name, model in self.base_models.items()]
        
        self.ensemble_model = VotingClassifier(
            estimators=estimators,
            voting='soft',
            weights=weights
        )
        
        # アンサンブルモデルの学習
        self.ensemble_model.fit(X_train, y_train)
        
        # 評価
        results = self._evaluate_ensemble(X_train, y_train, X_val, y_val)
        results['individual_performances'] = model_performances
        results['model_weights'] = self.model_weights
        
        return results
    
    def _train_stacking_ensemble(self, X_train: pd.DataFrame, y_train: np.ndarray,
                                X_val: Optional[pd.DataFrame] = None,
                                y_val: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Stacking Ensembleの学習"""
        
        # メタ学習器
        meta_learner = LogisticRegression(
            C=1.0,
            max_iter=1000,
            random_state=42
        )
        
        # Stacking Classifierの作成
        estimators = [(name, model) for name, model in self.base_models.items()]
        
        self.ensemble_model = StackingClassifier(
            estimators=estimators,
            final_estimator=meta_learner,
            cv=5,  # クロスバリデーション
            stack_method='predict_proba',
            n_jobs=-1
        )
        
        # 学習
        logger.info("Training stacking ensemble...")
        self.ensemble_model.fit(X_train, y_train)
        
        # 評価
        results = self._evaluate_ensemble(X_train, y_train, X_val, y_val)
        
        # 各レベルのモデルの寄与度分析
        results['layer_contributions'] = self._analyze_layer_contributions(X_val, y_val)
        
        return results
    
    def _train_blending_ensemble(self, X_train: pd.DataFrame, y_train: np.ndarray,
                                X_val: Optional[pd.DataFrame] = None,
                                y_val: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Blending Ensembleの学習"""
        
        # データ分割（ブレンド用）
        blend_split = int(len(X_train) * 0.8)
        X_blend_train = X_train[:blend_split]
        y_blend_train = y_train[:blend_split]
        X_blend_val = X_train[blend_split:]
        y_blend_val = y_train[blend_split:]
        
        # ベースモデルの学習と予測
        blend_features = []
        
        for name, model in self.base_models.items():
            logger.info(f"Training {name} for blending...")
            
            # 学習
            model.fit(X_blend_train, y_blend_train)
            
            # ブレンド用特徴量の生成
            blend_pred = model.predict_proba(X_blend_val)[:, 1]
            blend_features.append(blend_pred)
        
        # ブレンド特徴量の結合
        blend_features = np.column_stack(blend_features)
        
        # メタモデルの学習
        meta_model = LogisticRegression(C=1.0, max_iter=1000, random_state=42)
        meta_model.fit(blend_features, y_blend_val)
        
        # 全データで再学習
        for name, model in self.base_models.items():
            model.fit(X_train, y_train)
        
        # カスタムアンサンブルモデルの保存
        self.ensemble_model = {
            'base_models': self.base_models,
            'meta_model': meta_model,
            'type': 'blending'
        }
        
        # 評価
        results = self._evaluate_blending(X_train, y_train, X_val, y_val)
        
        return results
    
    def _train_advanced_ensemble(self, X_train: pd.DataFrame, y_train: np.ndarray,
                                X_val: Optional[pd.DataFrame] = None,
                                y_val: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """高度なアンサンブル（動的重み付け）"""
        
        # 各モデルの特徴量重要度を計算
        feature_importances = {}
        model_specializations = {}
        
        for name, model in self.base_models.items():
            logger.info(f"Analyzing {name} specialization...")
            
            # 学習
            model.fit(X_train, y_train)
            
            # 特徴量重要度
            if hasattr(model, 'feature_importances_'):
                feature_importances[name] = model.feature_importances_
            
            # モデルの得意分野を分析
            cv_folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
            fold_performances = []
            
            for train_idx, val_idx in cv_folds.split(X_train, y_train):
                X_fold_train = X_train.iloc[train_idx]
                y_fold_train = y_train[train_idx]
                X_fold_val = X_train.iloc[val_idx]
                y_fold_val = y_train[val_idx]
                
                # サブセットでの学習と評価
                temp_model = model.__class__(**model.get_params())
                temp_model.fit(X_fold_train, y_fold_train)
                
                fold_pred = temp_model.predict(X_fold_val)
                fold_f1 = f1_score(y_fold_val, fold_pred)
                fold_performances.append(fold_f1)
            
            model_specializations[name] = {
                'mean_performance': np.mean(fold_performances),
                'std_performance': np.std(fold_performances),
                'consistency': 1 / (np.std(fold_performances) + 0.01)
            }
        
        # 動的重み計算
        self.model_weights = self._calculate_dynamic_weights(model_specializations)
        
        # カスタムアンサンブル
        self.ensemble_model = {
            'base_models': self.base_models,
            'weights': self.model_weights,
            'feature_importances': feature_importances,
            'type': 'advanced'
        }
        
        # 評価
        results = self._evaluate_advanced(X_train, y_train, X_val, y_val)
        results['model_specializations'] = model_specializations
        
        return results
    
    def _calculate_dynamic_weights(self, specializations: Dict) -> Dict[str, float]:
        """動的重み計算"""
        weights = {}
        
        for name, spec in specializations.items():
            # パフォーマンスと一貫性を考慮した重み
            weight = spec['mean_performance'] * spec['consistency']
            weights[name] = weight
        
        # 正規化
        total = sum(weights.values())
        weights = {k: v/total for k, v in weights.items()}
        
        return weights
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        予測実行
        
        Args:
            X: 予測データ
        
        Returns:
            予測結果
        """
        if self.ensemble_model is None:
            raise ValueError("Model not trained yet")
        
        if isinstance(self.ensemble_model, dict):
            # カスタムアンサンブルの場合
            if self.ensemble_model['type'] == 'blending':
                return self._predict_blending(X)
            elif self.ensemble_model['type'] == 'advanced':
                return self._predict_advanced(X)
        else:
            # scikit-learnのアンサンブルモデル
            return self.ensemble_model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        確率予測
        
        Args:
            X: 予測データ
        
        Returns:
            予測確率
        """
        if self.ensemble_model is None:
            raise ValueError("Model not trained yet")
        
        if isinstance(self.ensemble_model, dict):
            # カスタムアンサンブルの場合
            if self.ensemble_model['type'] == 'blending':
                return self._predict_proba_blending(X)
            elif self.ensemble_model['type'] == 'advanced':
                return self._predict_proba_advanced(X)
        else:
            # scikit-learnのアンサンブルモデル
            return self.ensemble_model.predict_proba(X)
    
    def _predict_blending(self, X: pd.DataFrame) -> np.ndarray:
        """Blendingでの予測"""
        blend_features = []
        
        for name, model in self.ensemble_model['base_models'].items():
            pred = model.predict_proba(X)[:, 1]
            blend_features.append(pred)
        
        blend_features = np.column_stack(blend_features)
        return self.ensemble_model['meta_model'].predict(blend_features)
    
    def _predict_proba_blending(self, X: pd.DataFrame) -> np.ndarray:
        """Blendingでの確率予測"""
        blend_features = []
        
        for name, model in self.ensemble_model['base_models'].items():
            pred = model.predict_proba(X)[:, 1]
            blend_features.append(pred)
        
        blend_features = np.column_stack(blend_features)
        return self.ensemble_model['meta_model'].predict_proba(blend_features)
    
    def _predict_advanced(self, X: pd.DataFrame) -> np.ndarray:
        """高度なアンサンブルでの予測"""
        predictions = []
        weights = []
        
        for name, model in self.ensemble_model['base_models'].items():
            pred = model.predict(X)
            predictions.append(pred)
            weights.append(self.ensemble_model['weights'][name])
        
        # 重み付き多数決
        predictions = np.array(predictions).T
        weights = np.array(weights)
        
        weighted_predictions = []
        for row in predictions:
            weighted_sum = np.sum(row * weights)
            weighted_predictions.append(1 if weighted_sum > 0.5 else 0)
        
        return np.array(weighted_predictions)
    
    def _predict_proba_advanced(self, X: pd.DataFrame) -> np.ndarray:
        """高度なアンサンブルでの確率予測"""
        probabilities = []
        weights = []
        
        for name, model in self.ensemble_model['base_models'].items():
            proba = model.predict_proba(X)[:, 1]
            probabilities.append(proba)
            weights.append(self.ensemble_model['weights'][name])
        
        # 重み付き平均
        probabilities = np.array(probabilities).T
        weights = np.array(weights)
        
        weighted_proba = np.average(probabilities, axis=1, weights=weights)
        
        # 2クラス分類用の確率配列に変換
        return np.column_stack([1 - weighted_proba, weighted_proba])
    
    def _evaluate_ensemble(self, X_train: pd.DataFrame, y_train: np.ndarray,
                          X_val: Optional[pd.DataFrame] = None,
                          y_val: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """アンサンブルモデルの評価"""
        results = {}
        
        # 訓練データでの評価
        train_pred = self.predict(X_train)
        train_proba = self.predict_proba(X_train)[:, 1]
        
        results['train'] = {
            'accuracy': accuracy_score(y_train, train_pred),
            'precision': precision_score(y_train, train_pred),
            'recall': recall_score(y_train, train_pred),
            'f1': f1_score(y_train, train_pred),
            'auc': roc_auc_score(y_train, train_proba)
        }
        
        # 検証データでの評価
        if X_val is not None and y_val is not None:
            val_pred = self.predict(X_val)
            val_proba = self.predict_proba(X_val)[:, 1]
            
            results['validation'] = {
                'accuracy': accuracy_score(y_val, val_pred),
                'precision': precision_score(y_val, val_pred),
                'recall': recall_score(y_val, val_pred),
                'f1': f1_score(y_val, val_pred),
                'auc': roc_auc_score(y_val, val_proba),
                'confusion_matrix': confusion_matrix(y_val, val_pred).tolist()
            }
        
        return results
    
    def _evaluate_blending(self, X_train: pd.DataFrame, y_train: np.ndarray,
                          X_val: Optional[pd.DataFrame] = None,
                          y_val: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Blendingモデルの評価"""
        return self._evaluate_ensemble(X_train, y_train, X_val, y_val)
    
    def _evaluate_advanced(self, X_train: pd.DataFrame, y_train: np.ndarray,
                          X_val: Optional[pd.DataFrame] = None,
                          y_val: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """高度なアンサンブルの評価"""
        return self._evaluate_ensemble(X_train, y_train, X_val, y_val)
    
    def _analyze_layer_contributions(self, X: pd.DataFrame, y: np.ndarray) -> Dict:
        """レイヤー寄与度分析（Stacking用）"""
        if not hasattr(self.ensemble_model, 'transform'):
            return {}
        
        # 第1層の出力を取得
        first_layer_output = self.ensemble_model.transform(X)
        
        # 各ベースモデルの寄与度を計算
        contributions = {}
        for i, (name, _) in enumerate(self.ensemble_model.estimators):
            correlation = np.corrcoef(first_layer_output[:, i], y)[0, 1]
            contributions[name] = abs(correlation)
        
        return contributions
    
    def get_feature_importance(self, feature_names: List[str]) -> pd.DataFrame:
        """
        統合特徴量重要度の取得
        
        Args:
            feature_names: 特徴量名リスト
        
        Returns:
            特徴量重要度DataFrame
        """
        importance_dict = {}
        
        for name, model in self.base_models.items():
            if hasattr(model, 'feature_importances_'):
                importance_dict[name] = model.feature_importances_
        
        # 重み付き平均で統合
        if self.model_weights:
            weighted_importance = np.zeros(len(feature_names))
            for name, importance in importance_dict.items():
                weight = self.model_weights.get(name, 1/len(importance_dict))
                weighted_importance += importance * weight
        else:
            # 単純平均
            weighted_importance = np.mean(list(importance_dict.values()), axis=0)
        
        # DataFrameに変換
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': weighted_importance
        })
        importance_df = importance_df.sort_values('importance', ascending=False)
        
        return importance_df
    
    def save_model(self, filepath: str):
        """モデル保存"""
        joblib.dump({
            'ensemble_type': self.ensemble_type,
            'ensemble_model': self.ensemble_model,
            'base_models': self.base_models,
            'model_weights': self.model_weights,
            'performance_metrics': self.performance_metrics
        }, filepath)
        
        logger.info(f"Ensemble model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """モデル読み込み"""
        data = joblib.load(filepath)
        
        self.ensemble_type = data['ensemble_type']
        self.ensemble_model = data['ensemble_model']
        self.base_models = data['base_models']
        self.model_weights = data['model_weights']
        self.performance_metrics = data['performance_metrics']
        
        logger.info(f"Ensemble model loaded from {filepath}")