#!/usr/bin/env python
"""
Hyperparameter Optimization Module
Optunaを使用したベイズ最適化によるハイパーパラメータチューニング
"""

import optuna
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import xgboost as xgb
import lightgbm as lgb
import joblib
import json
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HyperparameterOptimizer:
    """ハイパーパラメータ最適化クラス"""
    
    def __init__(self, model_type: str = 'random_forest', n_trials: int = 100):
        """
        初期化
        
        Args:
            model_type: モデルの種類 ('random_forest', 'xgboost', 'lightgbm')
            n_trials: Optunaの試行回数
        """
        self.model_type = model_type
        self.n_trials = n_trials
        self.study = None
        self.best_params = None
        self.best_model = None
        self.optimization_history = []
        
    def create_objective(self, X: pd.DataFrame, y: np.ndarray, cv_folds: int = 5):
        """
        Optuna用の目的関数を作成
        
        Args:
            X: 特徴量データ
            y: ターゲット
            cv_folds: クロスバリデーションのfold数
        
        Returns:
            目的関数
        """
        def objective(trial):
            # モデルタイプに応じたパラメータ空間定義
            if self.model_type == 'random_forest':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                    'max_depth': trial.suggest_int('max_depth', 3, 30),
                    'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                    'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                    'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2', None]),
                    'bootstrap': trial.suggest_categorical('bootstrap', [True, False]),
                    'class_weight': trial.suggest_categorical('class_weight', ['balanced', None])
                }
                model = RandomForestClassifier(**params, random_state=42, n_jobs=-1)
                
            elif self.model_type == 'xgboost':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                    'max_depth': trial.suggest_int('max_depth', 3, 15),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                    'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                    'gamma': trial.suggest_float('gamma', 0, 5),
                    'reg_alpha': trial.suggest_float('reg_alpha', 0, 2),
                    'reg_lambda': trial.suggest_float('reg_lambda', 0, 2),
                }
                model = xgb.XGBClassifier(
                    **params,
                    objective='binary:logistic',
                    eval_metric='logloss',
                    random_state=42,
                    n_jobs=-1
                )
                
            elif self.model_type == 'lightgbm':
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 500),
                    'num_leaves': trial.suggest_int('num_leaves', 10, 200),
                    'max_depth': trial.suggest_int('max_depth', 3, 15),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'feature_fraction': trial.suggest_float('feature_fraction', 0.5, 1.0),
                    'bagging_fraction': trial.suggest_float('bagging_fraction', 0.5, 1.0),
                    'bagging_freq': trial.suggest_int('bagging_freq', 1, 10),
                    'lambda_l1': trial.suggest_float('lambda_l1', 0, 2),
                    'lambda_l2': trial.suggest_float('lambda_l2', 0, 2),
                }
                model = lgb.LGBMClassifier(
                    **params,
                    objective='binary',
                    metric='binary_logloss',
                    random_state=42,
                    n_jobs=-1,
                    verbose=-1
                )
            else:
                raise ValueError(f"Unsupported model type: {self.model_type}")
            
            # クロスバリデーションで評価
            cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=42)
            scores = cross_val_score(model, X, y, cv=cv, scoring='f1', n_jobs=-1)
            
            # 平均F1スコアを返す（最大化）
            return scores.mean()
        
        return objective
    
    def optimize(self, X_train: pd.DataFrame, y_train: np.ndarray, 
                X_val: Optional[pd.DataFrame] = None, y_val: Optional[np.ndarray] = None) -> Dict:
        """
        ハイパーパラメータ最適化を実行
        
        Args:
            X_train: 訓練データの特徴量
            y_train: 訓練データのターゲット
            X_val: 検証データの特徴量（オプション）
            y_val: 検証データのターゲット（オプション）
        
        Returns:
            最適化結果
        """
        logger.info(f"Starting hyperparameter optimization for {self.model_type}")
        logger.info(f"Training data shape: {X_train.shape}")
        
        # Optuna Studyの作成
        self.study = optuna.create_study(
            direction='maximize',
            study_name=f'{self.model_type}_optimization_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        )
        
        # 目的関数の作成
        objective = self.create_objective(X_train, y_train)
        
        # 最適化実行
        self.study.optimize(
            objective, 
            n_trials=self.n_trials,
            callbacks=[self._optimization_callback]
        )
        
        # 最良パラメータ取得
        self.best_params = self.study.best_params
        logger.info(f"Best parameters: {self.best_params}")
        logger.info(f"Best F1 score: {self.study.best_value:.4f}")
        
        # 最良モデルの訓練
        self.best_model = self._train_best_model(X_train, y_train)
        
        # 検証データでの評価
        results = {
            'best_params': self.best_params,
            'best_cv_score': self.study.best_value,
            'n_trials': len(self.study.trials),
            'model_type': self.model_type
        }
        
        if X_val is not None and y_val is not None:
            val_metrics = self._evaluate_model(self.best_model, X_val, y_val)
            results['validation_metrics'] = val_metrics
            logger.info(f"Validation metrics: {val_metrics}")
        
        # 最適化履歴の保存
        self._save_optimization_history()
        
        return results
    
    def _train_best_model(self, X: pd.DataFrame, y: np.ndarray):
        """
        最良パラメータでモデルを訓練
        
        Args:
            X: 特徴量データ
            y: ターゲット
        
        Returns:
            訓練済みモデル
        """
        if self.model_type == 'random_forest':
            model = RandomForestClassifier(**self.best_params, random_state=42, n_jobs=-1)
        elif self.model_type == 'xgboost':
            model = xgb.XGBClassifier(
                **self.best_params,
                objective='binary:logistic',
                eval_metric='logloss',
                random_state=42,
                n_jobs=-1
            )
        elif self.model_type == 'lightgbm':
            model = lgb.LGBMClassifier(
                **self.best_params,
                objective='binary',
                metric='binary_logloss',
                random_state=42,
                n_jobs=-1,
                verbose=-1
            )
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
        model.fit(X, y)
        return model
    
    def _evaluate_model(self, model, X: pd.DataFrame, y: np.ndarray) -> Dict:
        """
        モデルを評価
        
        Args:
            model: 評価するモデル
            X: 特徴量データ
            y: ターゲット
        
        Returns:
            評価メトリクス
        """
        y_pred = model.predict(X)
        
        return {
            'accuracy': accuracy_score(y, y_pred),
            'precision': precision_score(y, y_pred),
            'recall': recall_score(y, y_pred),
            'f1': f1_score(y, y_pred)
        }
    
    def _optimization_callback(self, study, trial):
        """
        最適化中のコールバック関数
        
        Args:
            study: Optunaのstudyオブジェクト
            trial: 現在のtrial
        """
        self.optimization_history.append({
            'trial': trial.number,
            'value': trial.value,
            'params': trial.params,
            'datetime': datetime.now().isoformat()
        })
        
        if trial.number % 10 == 0:
            logger.info(f"Trial {trial.number}: F1={trial.value:.4f}")
    
    def _save_optimization_history(self):
        """最適化履歴を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"optimization_history_{self.model_type}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                'model_type': self.model_type,
                'best_params': self.best_params,
                'best_value': self.study.best_value,
                'n_trials': self.n_trials,
                'history': self.optimization_history
            }, f, indent=2, default=str)
        
        logger.info(f"Optimization history saved to {filename}")
    
    def compare_models(self, X_train: pd.DataFrame, y_train: np.ndarray,
                      X_val: pd.DataFrame, y_val: np.ndarray,
                      model_types: List[str] = ['random_forest', 'xgboost', 'lightgbm']) -> pd.DataFrame:
        """
        複数のモデルを比較
        
        Args:
            X_train: 訓練データの特徴量
            y_train: 訓練データのターゲット
            X_val: 検証データの特徴量
            y_val: 検証データのターゲット
            model_types: 比較するモデルタイプのリスト
        
        Returns:
            比較結果のDataFrame
        """
        results = []
        
        for model_type in model_types:
            logger.info(f"\nOptimizing {model_type}...")
            
            # 新しいオプティマイザインスタンス作成
            optimizer = HyperparameterOptimizer(
                model_type=model_type,
                n_trials=self.n_trials
            )
            
            # 最適化実行
            opt_results = optimizer.optimize(X_train, y_train, X_val, y_val)
            
            # 結果を追加
            results.append({
                'model_type': model_type,
                'best_cv_f1': opt_results['best_cv_score'],
                'val_accuracy': opt_results['validation_metrics']['accuracy'],
                'val_precision': opt_results['validation_metrics']['precision'],
                'val_recall': opt_results['validation_metrics']['recall'],
                'val_f1': opt_results['validation_metrics']['f1'],
                'n_trials': opt_results['n_trials']
            })
        
        # DataFrameに変換
        comparison_df = pd.DataFrame(results)
        comparison_df = comparison_df.sort_values('val_f1', ascending=False)
        
        logger.info("\nModel Comparison Results:")
        logger.info(comparison_df.to_string())
        
        # 最良モデルの保存
        best_model_type = comparison_df.iloc[0]['model_type']
        logger.info(f"\nBest model: {best_model_type}")
        
        return comparison_df
    
    def save_model(self, filepath: str):
        """
        モデルを保存
        
        Args:
            filepath: 保存先パス
        """
        if self.best_model is None:
            raise ValueError("No model to save. Run optimize() first.")
        
        joblib.dump({
            'model': self.best_model,
            'params': self.best_params,
            'model_type': self.model_type
        }, filepath)
        
        logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """
        モデルを読み込み
        
        Args:
            filepath: 読み込み元パス
        """
        data = joblib.load(filepath)
        self.best_model = data['model']
        self.best_params = data['params']
        self.model_type = data['model_type']
        
        logger.info(f"Model loaded from {filepath}")
    
    def get_feature_importance(self, feature_names: List[str]) -> pd.DataFrame:
        """
        特徴量の重要度を取得
        
        Args:
            feature_names: 特徴量名のリスト
        
        Returns:
            特徴量重要度のDataFrame
        """
        if self.best_model is None:
            raise ValueError("No model available. Run optimize() first.")
        
        if hasattr(self.best_model, 'feature_importances_'):
            importance = self.best_model.feature_importances_
        else:
            raise ValueError(f"Model type {self.model_type} doesn't support feature importance")
        
        # DataFrameに変換
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance': importance
        })
        importance_df = importance_df.sort_values('importance', ascending=False)
        
        return importance_df
    
    def plot_optimization_history(self):
        """最適化履歴をプロット"""
        if self.study is None:
            raise ValueError("No study available. Run optimize() first.")
        
        try:
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            # 最適化履歴のプロット
            fig = make_subplots(
                rows=2, cols=1,
                subplot_titles=('Optimization History', 'Parameter Importance'),
                vertical_spacing=0.15
            )
            
            # 履歴プロット
            trials = [t.number for t in self.study.trials]
            values = [t.value for t in self.study.trials]
            
            fig.add_trace(
                go.Scatter(x=trials, y=values, mode='markers+lines',
                          name='Trial Value',
                          marker=dict(size=8, color=values, colorscale='Viridis')),
                row=1, col=1
            )
            
            # ベストバリューのライン
            best_values = [max(values[:i+1]) for i in range(len(values))]
            fig.add_trace(
                go.Scatter(x=trials, y=best_values, mode='lines',
                          name='Best Value',
                          line=dict(color='red', width=2, dash='dash')),
                row=1, col=1
            )
            
            # パラメータ重要度
            if hasattr(optuna.importance, 'get_param_importances'):
                importances = optuna.importance.get_param_importances(self.study)
                params = list(importances.keys())
                importance_values = list(importances.values())
                
                fig.add_trace(
                    go.Bar(x=importance_values, y=params, orientation='h',
                          marker=dict(color='lightblue')),
                    row=2, col=1
                )
            
            fig.update_layout(
                title=f'{self.model_type} Hyperparameter Optimization Results',
                height=800,
                showlegend=True
            )
            
            return fig
            
        except ImportError:
            logger.warning("Plotly not available for visualization")
            return None


class AutoML:
    """自動機械学習クラス"""
    
    def __init__(self, n_trials: int = 50):
        """
        初期化
        
        Args:
            n_trials: 各モデルの試行回数
        """
        self.n_trials = n_trials
        self.best_model = None
        self.best_model_type = None
        self.results = None
        
    def fit(self, X_train: pd.DataFrame, y_train: np.ndarray,
           X_val: pd.DataFrame, y_val: np.ndarray) -> Dict:
        """
        自動的に最良のモデルを選択して訓練
        
        Args:
            X_train: 訓練データの特徴量
            y_train: 訓練データのターゲット
            X_val: 検証データの特徴量
            y_val: 検証データのターゲット
        
        Returns:
            最適化結果
        """
        logger.info("Starting AutoML process...")
        
        # 複数モデルの比較
        optimizer = HyperparameterOptimizer(n_trials=self.n_trials)
        comparison_df = optimizer.compare_models(X_train, y_train, X_val, y_val)
        
        # 最良モデルの選択
        best_row = comparison_df.iloc[0]
        self.best_model_type = best_row['model_type']
        
        # 最良モデルの再訓練（より多くのtrialsで）
        logger.info(f"\nRetraining best model ({self.best_model_type}) with more trials...")
        final_optimizer = HyperparameterOptimizer(
            model_type=self.best_model_type,
            n_trials=self.n_trials * 2  # より詳細な最適化
        )
        
        final_results = final_optimizer.optimize(X_train, y_train, X_val, y_val)
        self.best_model = final_optimizer.best_model
        
        # 結果の保存
        self.results = {
            'comparison': comparison_df.to_dict(),
            'best_model_type': self.best_model_type,
            'best_model_params': final_results['best_params'],
            'best_model_metrics': final_results['validation_metrics']
        }
        
        logger.info(f"\nAutoML completed. Best model: {self.best_model_type}")
        logger.info(f"Best validation F1 score: {final_results['validation_metrics']['f1']:.4f}")
        
        return self.results
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        予測を実行
        
        Args:
            X: 予測用データ
        
        Returns:
            予測結果
        """
        if self.best_model is None:
            raise ValueError("No model available. Run fit() first.")
        
        return self.best_model.predict(X)
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """
        確率予測を実行
        
        Args:
            X: 予測用データ
        
        Returns:
            予測確率
        """
        if self.best_model is None:
            raise ValueError("No model available. Run fit() first.")
        
        return self.best_model.predict_proba(X)