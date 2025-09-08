#!/usr/bin/env python
"""
Continuous Learning Pipeline
モデルの継続的学習パイプライン
"""

import os
import json
import pickle
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
import logging
import numpy as np
import pandas as pd
from pathlib import Path

# MLライブラリ
try:
    from sklearn.model_selection import train_test_split, cross_val_score
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
    from sklearn.ensemble import RandomForestClassifier
    import xgboost as xgb
    import lightgbm as lgb
    ADVANCED_ML_AVAILABLE = True
except ImportError:
    ADVANCED_ML_AVAILABLE = False

# 並列処理
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import asyncio

# モニタリング
try:
    import mlflow
    import mlflow.sklearn
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


class ModelVersionManager:
    """モデルバージョン管理クラス"""
    
    def __init__(self, model_dir: str = "models/"):
        """初期化"""
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.versions_file = self.model_dir / "versions.json"
        self.versions = self._load_versions()
    
    def _load_versions(self) -> Dict:
        """バージョン情報読み込み"""
        if self.versions_file.exists():
            with open(self.versions_file, 'r') as f:
                return json.load(f)
        return {"models": [], "current": None}
    
    def save_model(self, model: Any, metrics: Dict, metadata: Dict) -> str:
        """
        モデル保存
        
        Args:
            model: 保存するモデル
            metrics: 評価メトリクス
            metadata: メタデータ
        
        Returns:
            バージョンID
        """
        # バージョンID生成
        version_id = self._generate_version_id()
        timestamp = datetime.now().isoformat()
        
        # モデルファイル保存
        model_file = self.model_dir / f"model_{version_id}.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model, f)
        
        # バージョン情報更新
        version_info = {
            "version_id": version_id,
            "timestamp": timestamp,
            "model_file": str(model_file),
            "metrics": metrics,
            "metadata": metadata,
            "status": "staged"
        }
        
        self.versions["models"].append(version_info)
        self._save_versions()
        
        logging.info(f"Model saved: {version_id}")
        return version_id
    
    def load_model(self, version_id: Optional[str] = None) -> Tuple[Any, Dict]:
        """
        モデル読み込み
        
        Args:
            version_id: バージョンID（Noneの場合は最新）
        
        Returns:
            モデルとメタデータ
        """
        if version_id is None:
            version_id = self.versions.get("current")
        
        if not version_id:
            raise ValueError("No model version specified or set as current")
        
        # バージョン情報取得
        version_info = self._get_version_info(version_id)
        if not version_info:
            raise ValueError(f"Version {version_id} not found")
        
        # モデル読み込み
        with open(version_info["model_file"], 'rb') as f:
            model = pickle.load(f)
        
        return model, version_info
    
    def promote_model(self, version_id: str) -> bool:
        """
        モデルを本番環境に昇格
        
        Args:
            version_id: バージョンID
        
        Returns:
            成功フラグ
        """
        version_info = self._get_version_info(version_id)
        if not version_info:
            return False
        
        # 既存の本番モデルをアーカイブ
        if self.versions["current"]:
            old_version = self._get_version_info(self.versions["current"])
            if old_version:
                old_version["status"] = "archived"
        
        # 新モデルを本番に設定
        version_info["status"] = "production"
        version_info["promoted_at"] = datetime.now().isoformat()
        self.versions["current"] = version_id
        
        self._save_versions()
        logging.info(f"Model {version_id} promoted to production")
        return True
    
    def rollback_model(self, steps: int = 1) -> bool:
        """
        モデルをロールバック
        
        Args:
            steps: ロールバックするステップ数
        
        Returns:
            成功フラグ
        """
        production_models = [
            m for m in self.versions["models"] 
            if m.get("promoted_at")
        ]
        
        if len(production_models) <= steps:
            logging.error("Not enough versions to rollback")
            return False
        
        # ソート（昇格日時順）
        production_models.sort(key=lambda x: x["promoted_at"], reverse=True)
        
        # ロールバック先を設定
        target_version = production_models[steps]
        return self.promote_model(target_version["version_id"])
    
    def _generate_version_id(self) -> str:
        """バージョンID生成"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = hashlib.md5(
            f"{timestamp}_{np.random.rand()}".encode()
        ).hexdigest()[:8]
        return f"v_{timestamp}_{random_suffix}"
    
    def _get_version_info(self, version_id: str) -> Optional[Dict]:
        """バージョン情報取得"""
        for version in self.versions["models"]:
            if version["version_id"] == version_id:
                return version
        return None
    
    def _save_versions(self):
        """バージョン情報保存"""
        with open(self.versions_file, 'w') as f:
            json.dump(self.versions, f, indent=2)


class DataDriftDetector:
    """データドリフト検出クラス"""
    
    def __init__(self, baseline_stats: Optional[Dict] = None):
        """初期化"""
        self.baseline_stats = baseline_stats or {}
        self.drift_history = []
    
    def calculate_statistics(self, data: pd.DataFrame) -> Dict:
        """
        統計情報計算
        
        Args:
            data: データフレーム
        
        Returns:
            統計情報
        """
        stats = {}
        
        for column in data.select_dtypes(include=[np.number]).columns:
            stats[column] = {
                "mean": data[column].mean(),
                "std": data[column].std(),
                "min": data[column].min(),
                "max": data[column].max(),
                "q25": data[column].quantile(0.25),
                "q50": data[column].quantile(0.50),
                "q75": data[column].quantile(0.75),
                "null_rate": data[column].isnull().mean()
            }
        
        return stats
    
    def detect_drift(self, new_data: pd.DataFrame, 
                     threshold: float = 0.1) -> Dict[str, Any]:
        """
        データドリフト検出
        
        Args:
            new_data: 新しいデータ
            threshold: ドリフト閾値
        
        Returns:
            ドリフト検出結果
        """
        if not self.baseline_stats:
            self.baseline_stats = self.calculate_statistics(new_data)
            return {"drift_detected": False, "message": "Baseline established"}
        
        new_stats = self.calculate_statistics(new_data)
        drift_scores = {}
        
        for column in new_stats:
            if column in self.baseline_stats:
                # KLダイバージェンス計算（簡易版）
                baseline = self.baseline_stats[column]
                current = new_stats[column]
                
                # 平均値の変化率
                mean_change = abs(current["mean"] - baseline["mean"]) / (baseline["mean"] + 1e-10)
                
                # 標準偏差の変化率
                std_change = abs(current["std"] - baseline["std"]) / (baseline["std"] + 1e-10)
                
                # ドリフトスコア
                drift_score = (mean_change + std_change) / 2
                drift_scores[column] = drift_score
        
        # 全体のドリフト判定
        max_drift = max(drift_scores.values()) if drift_scores else 0
        drift_detected = max_drift > threshold
        
        result = {
            "drift_detected": drift_detected,
            "max_drift_score": max_drift,
            "drift_scores": drift_scores,
            "timestamp": datetime.now().isoformat()
        }
        
        self.drift_history.append(result)
        
        if drift_detected:
            logging.warning(f"Data drift detected: {max_drift:.3f}")
        
        return result
    
    def update_baseline(self, new_data: pd.DataFrame):
        """ベースライン更新"""
        self.baseline_stats = self.calculate_statistics(new_data)
        logging.info("Baseline statistics updated")


class AutoRetrainer:
    """自動再学習クラス"""
    
    def __init__(self, 
                 model_manager: ModelVersionManager,
                 drift_detector: DataDriftDetector):
        """初期化"""
        self.model_manager = model_manager
        self.drift_detector = drift_detector
        self.retraining_history = []
    
    def evaluate_model(self, model: Any, X_test: np.ndarray, 
                      y_test: np.ndarray) -> Dict:
        """
        モデル評価
        
        Args:
            model: 評価するモデル
            X_test: テストデータ
            y_test: テストラベル
        
        Returns:
            評価メトリクス
        """
        y_pred = model.predict(X_test)
        
        # 二値分類の場合
        if len(np.unique(y_test)) == 2:
            metrics = {
                "accuracy": accuracy_score(y_test, y_pred),
                "precision": precision_score(y_test, y_pred),
                "recall": recall_score(y_test, y_pred),
                "f1": f1_score(y_test, y_pred)
            }
        else:
            metrics = {
                "accuracy": accuracy_score(y_test, y_pred)
            }
        
        return metrics
    
    def should_retrain(self, 
                       performance_drop: float,
                       drift_detected: bool,
                       last_retrain_days: int) -> bool:
        """
        再学習判定
        
        Args:
            performance_drop: 性能低下率
            drift_detected: ドリフト検出フラグ
            last_retrain_days: 前回再学習からの日数
        
        Returns:
            再学習実施フラグ
        """
        # 判定条件
        conditions = [
            performance_drop > 0.05,  # 5%以上の性能低下
            drift_detected,  # データドリフト検出
            last_retrain_days > 30  # 30日以上経過
        ]
        
        return any(conditions)
    
    async def retrain_model_async(self, 
                                  X_train: np.ndarray,
                                  y_train: np.ndarray,
                                  model_type: str = "random_forest") -> Dict:
        """
        非同期モデル再学習
        
        Args:
            X_train: 訓練データ
            y_train: 訓練ラベル
            model_type: モデルタイプ
        
        Returns:
            再学習結果
        """
        start_time = datetime.now()
        
        # データ分割
        X_train_split, X_val_split, y_train_split, y_val_split = train_test_split(
            X_train, y_train, test_size=0.2, random_state=42
        )
        
        # モデル学習
        if model_type == "random_forest":
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == "xgboost" and ADVANCED_ML_AVAILABLE:
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        elif model_type == "lightgbm" and ADVANCED_ML_AVAILABLE:
            model = lgb.LGBMClassifier(
                n_estimators=100,
                max_depth=10,
                learning_rate=0.1,
                random_state=42
            )
        else:
            model = RandomForestClassifier(n_estimators=50, random_state=42)
        
        # 学習実行
        model.fit(X_train_split, y_train_split)
        
        # 評価
        metrics = self.evaluate_model(model, X_val_split, y_val_split)
        
        # クロスバリデーション
        cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
        metrics['cv_mean'] = cv_scores.mean()
        metrics['cv_std'] = cv_scores.std()
        
        # 学習時間
        training_time = (datetime.now() - start_time).total_seconds()
        
        # メタデータ
        metadata = {
            "model_type": model_type,
            "training_samples": len(X_train),
            "training_time": training_time,
            "feature_count": X_train.shape[1],
            "retrain_reason": "scheduled"
        }
        
        # モデル保存
        version_id = self.model_manager.save_model(model, metrics, metadata)
        
        result = {
            "version_id": version_id,
            "metrics": metrics,
            "metadata": metadata,
            "status": "completed"
        }
        
        self.retraining_history.append(result)
        
        return result
    
    def schedule_retrain(self, X: np.ndarray, y: np.ndarray, 
                        interval_hours: int = 24) -> None:
        """
        定期再学習スケジューリング
        
        Args:
            X: 訓練データ
            y: 訓練ラベル
            interval_hours: 再学習間隔（時間）
        """
        import schedule
        import time
        
        def retrain_job():
            logging.info("Starting scheduled retraining...")
            
            # ドリフト検出
            df = pd.DataFrame(X)
            drift_result = self.drift_detector.detect_drift(df)
            
            # 再学習実施
            if drift_result["drift_detected"]:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.retrain_model_async(X, y)
                )
                logging.info(f"Retraining completed: {result['version_id']}")
        
        # スケジュール設定
        schedule.every(interval_hours).hours.do(retrain_job)
        
        logging.info(f"Retraining scheduled every {interval_hours} hours")


class ModelMonitor:
    """モデルモニタリングクラス"""
    
    def __init__(self):
        """初期化"""
        self.performance_history = []
        self.prediction_history = []
        self.alert_thresholds = {
            "accuracy_min": 0.8,
            "latency_max": 1.0,  # seconds
            "error_rate_max": 0.05
        }
    
    def log_prediction(self, 
                      input_data: Dict,
                      prediction: float,
                      confidence: float,
                      latency: float):
        """
        予測ログ記録
        
        Args:
            input_data: 入力データ
            prediction: 予測値
            confidence: 信頼度
            latency: レイテンシ
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "input_hash": hashlib.md5(
                json.dumps(input_data, sort_keys=True).encode()
            ).hexdigest(),
            "prediction": prediction,
            "confidence": confidence,
            "latency": latency
        }
        
        self.prediction_history.append(log_entry)
        
        # MLflow記録（可能な場合）
        if MLFLOW_AVAILABLE:
            mlflow.log_metrics({
                "prediction": prediction,
                "confidence": confidence,
                "latency": latency
            })
    
    def calculate_performance_metrics(self, 
                                     y_true: np.ndarray,
                                     y_pred: np.ndarray) -> Dict:
        """
        性能メトリクス計算
        
        Args:
            y_true: 実際の値
            y_pred: 予測値
        
        Returns:
            性能メトリクス
        """
        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "timestamp": datetime.now().isoformat()
        }
        
        # 二値分類の追加メトリクス
        if len(np.unique(y_true)) == 2:
            metrics.update({
                "precision": precision_score(y_true, y_pred),
                "recall": recall_score(y_true, y_pred),
                "f1": f1_score(y_true, y_pred)
            })
        
        self.performance_history.append(metrics)
        
        # アラートチェック
        if metrics["accuracy"] < self.alert_thresholds["accuracy_min"]:
            self._send_alert("Low accuracy detected", metrics)
        
        return metrics
    
    def get_monitoring_summary(self) -> Dict:
        """
        モニタリングサマリー取得
        
        Returns:
            サマリー情報
        """
        if not self.prediction_history:
            return {"status": "No predictions logged"}
        
        recent_predictions = self.prediction_history[-100:]  # 直近100件
        
        latencies = [p["latency"] for p in recent_predictions]
        confidences = [p["confidence"] for p in recent_predictions]
        
        summary = {
            "total_predictions": len(self.prediction_history),
            "recent_predictions": len(recent_predictions),
            "avg_latency": np.mean(latencies),
            "p95_latency": np.percentile(latencies, 95),
            "avg_confidence": np.mean(confidences),
            "min_confidence": np.min(confidences),
            "last_update": self.prediction_history[-1]["timestamp"]
        }
        
        if self.performance_history:
            recent_performance = self.performance_history[-1]
            summary["current_accuracy"] = recent_performance["accuracy"]
        
        return summary
    
    def _send_alert(self, message: str, data: Dict):
        """アラート送信"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "data": data,
            "severity": "warning"
        }
        
        logging.warning(f"Alert: {message} - {data}")
        
        # 実際の実装では、メール/Slack通知等を追加
        # send_email_notification(alert)
        # send_slack_notification(alert)


class ContinuousLearningPipeline:
    """継続的学習パイプライン統合クラス"""
    
    def __init__(self, model_dir: str = "models/"):
        """初期化"""
        self.model_manager = ModelVersionManager(model_dir)
        self.drift_detector = DataDriftDetector()
        self.auto_retrainer = AutoRetrainer(
            self.model_manager, 
            self.drift_detector
        )
        self.monitor = ModelMonitor()
        self.is_running = False
    
    async def run_pipeline(self, 
                          X_train: np.ndarray,
                          y_train: np.ndarray,
                          X_new: Optional[np.ndarray] = None,
                          y_new: Optional[np.ndarray] = None):
        """
        パイプライン実行
        
        Args:
            X_train: 初期訓練データ
            y_train: 初期訓練ラベル
            X_new: 新規データ（オプション）
            y_new: 新規ラベル（オプション）
        """
        self.is_running = True
        
        try:
            # 1. ベースラインモデル学習
            logging.info("Training baseline model...")
            result = await self.auto_retrainer.retrain_model_async(
                X_train, y_train
            )
            baseline_version = result["version_id"]
            
            # 2. モデルを本番環境に昇格
            self.model_manager.promote_model(baseline_version)
            
            # 3. ベースライン統計設定
            df_train = pd.DataFrame(X_train)
            self.drift_detector.baseline_stats = \
                self.drift_detector.calculate_statistics(df_train)
            
            # 4. 新規データがある場合の処理
            if X_new is not None and y_new is not None:
                logging.info("Processing new data...")
                
                # ドリフト検出
                df_new = pd.DataFrame(X_new)
                drift_result = self.drift_detector.detect_drift(df_new)
                
                # 現行モデルの性能評価
                current_model, _ = self.model_manager.load_model()
                metrics_new = self.auto_retrainer.evaluate_model(
                    current_model, X_new, y_new
                )
                
                # モニタリング記録
                self.monitor.calculate_performance_metrics(
                    y_new, current_model.predict(X_new)
                )
                
                # 再学習判定
                baseline_metrics = result["metrics"]
                performance_drop = (
                    baseline_metrics["accuracy"] - metrics_new["accuracy"]
                ) / baseline_metrics["accuracy"]
                
                should_retrain = self.auto_retrainer.should_retrain(
                    performance_drop=performance_drop,
                    drift_detected=drift_result["drift_detected"],
                    last_retrain_days=0
                )
                
                if should_retrain:
                    logging.info("Retraining triggered...")
                    
                    # データ結合
                    X_combined = np.vstack([X_train, X_new])
                    y_combined = np.hstack([y_train, y_new])
                    
                    # 再学習
                    retrain_result = await self.auto_retrainer.retrain_model_async(
                        X_combined, y_combined
                    )
                    
                    # A/Bテスト（簡易版）
                    if retrain_result["metrics"]["accuracy"] > metrics_new["accuracy"]:
                        self.model_manager.promote_model(
                            retrain_result["version_id"]
                        )
                        logging.info("New model promoted")
                    else:
                        logging.info("Keeping current model")
            
            # 5. サマリー生成
            summary = {
                "pipeline_status": "completed",
                "baseline_version": baseline_version,
                "current_version": self.model_manager.versions["current"],
                "monitoring_summary": self.monitor.get_monitoring_summary(),
                "drift_history": self.drift_detector.drift_history[-5:]
            }
            
            return summary
            
        finally:
            self.is_running = False
    
    def get_status(self) -> Dict:
        """パイプラインステータス取得"""
        return {
            "is_running": self.is_running,
            "current_model": self.model_manager.versions.get("current"),
            "total_versions": len(self.model_manager.versions["models"]),
            "monitoring": self.monitor.get_monitoring_summary()
        }


# 使用例
if __name__ == "__main__":
    # ロギング設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # サンプルデータ生成
    from sklearn.datasets import make_classification
    
    X_train, y_train = make_classification(
        n_samples=1000,
        n_features=20,
        n_informative=15,
        random_state=42
    )
    
    X_new, y_new = make_classification(
        n_samples=200,
        n_features=20,
        n_informative=15,
        random_state=43
    )
    
    # パイプライン実行
    pipeline = ContinuousLearningPipeline()
    
    # 非同期実行
    async def main():
        result = await pipeline.run_pipeline(
            X_train, y_train, X_new, y_new
        )
        print("\nPipeline Result:")
        print(json.dumps(result, indent=2, default=str))
    
    asyncio.run(main())