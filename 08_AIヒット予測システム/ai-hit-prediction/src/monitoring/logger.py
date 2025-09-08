#!/usr/bin/env python
"""
Centralized Logging and Monitoring Module
集中ロギングと監視システム
"""

import logging
import json
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import os

# Structured logging
from pythonjsonlogger import jsonlogger

# Monitoring integrations
try:
    from prometheus_client import Counter, Histogram, Gauge, Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


class MetricsCollector:
    """メトリクス収集クラス"""
    
    def __init__(self):
        """初期化"""
        if PROMETHEUS_AVAILABLE:
            # カウンターメトリクス
            self.prediction_counter = Counter(
                'ai_hit_predictions_total',
                'Total number of predictions',
                ['model_type', 'status']
            )
            
            self.api_requests_counter = Counter(
                'api_requests_total',
                'Total API requests',
                ['method', 'endpoint', 'status']
            )
            
            self.error_counter = Counter(
                'application_errors_total',
                'Total application errors',
                ['error_type', 'severity']
            )
            
            # ヒストグラムメトリクス
            self.prediction_duration = Histogram(
                'prediction_duration_seconds',
                'Prediction processing time',
                ['model_type']
            )
            
            self.api_response_time = Histogram(
                'api_response_time_seconds',
                'API response time',
                ['endpoint']
            )
            
            # ゲージメトリクス
            self.model_accuracy = Gauge(
                'model_accuracy',
                'Current model accuracy',
                ['model_type']
            )
            
            self.active_users = Gauge(
                'active_users',
                'Number of active users'
            )
            
            self.cache_hit_ratio = Gauge(
                'cache_hit_ratio',
                'Cache hit ratio'
            )
            
            # サマリーメトリクス
            self.feature_extraction_time = Summary(
                'feature_extraction_time_seconds',
                'Feature extraction processing time'
            )
            
            self.batch_processing_time = Summary(
                'batch_processing_time_seconds',
                'Batch processing time'
            )
    
    def record_prediction(self, model_type: str, status: str, duration: float):
        """予測メトリクス記録"""
        if PROMETHEUS_AVAILABLE:
            self.prediction_counter.labels(model_type=model_type, status=status).inc()
            self.prediction_duration.labels(model_type=model_type).observe(duration)
    
    def record_api_request(self, method: str, endpoint: str, status: int, duration: float):
        """APIリクエストメトリクス記録"""
        if PROMETHEUS_AVAILABLE:
            self.api_requests_counter.labels(
                method=method,
                endpoint=endpoint,
                status=str(status)
            ).inc()
            self.api_response_time.labels(endpoint=endpoint).observe(duration)
    
    def record_error(self, error_type: str, severity: str = "error"):
        """エラーメトリクス記録"""
        if PROMETHEUS_AVAILABLE:
            self.error_counter.labels(error_type=error_type, severity=severity).inc()
    
    def set_model_accuracy(self, model_type: str, accuracy: float):
        """モデル精度設定"""
        if PROMETHEUS_AVAILABLE:
            self.model_accuracy.labels(model_type=model_type).set(accuracy)
    
    def set_active_users(self, count: int):
        """アクティブユーザー数設定"""
        if PROMETHEUS_AVAILABLE:
            self.active_users.set(count)
    
    def set_cache_hit_ratio(self, ratio: float):
        """キャッシュヒット率設定"""
        if PROMETHEUS_AVAILABLE:
            self.cache_hit_ratio.set(ratio)


class StructuredLogger:
    """構造化ログクラス"""
    
    def __init__(self, name: str, log_level: str = "INFO"):
        """
        初期化
        
        Args:
            name: ロガー名
            log_level: ログレベル
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level))
        self.logger.handlers.clear()
        
        # JSON形式のフォーマッター
        json_formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s',
            rename_fields={'levelname': 'level', 'name': 'logger'}
        )
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(json_formatter)
        self.logger.addHandler(console_handler)
        
        # ファイルハンドラー
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(json_formatter)
        self.logger.addHandler(file_handler)
        
        # Sentry統合
        if SENTRY_AVAILABLE and os.getenv("SENTRY_DSN"):
            sentry_logging = LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            )
            sentry_sdk.init(
                dsn=os.getenv("SENTRY_DSN"),
                integrations=[sentry_logging],
                traces_sample_rate=0.1,
                environment=os.getenv("ENVIRONMENT", "development")
            )
    
    def _add_context(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """コンテキスト情報追加"""
        context = {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': os.getenv('ENVIRONMENT', 'development'),
            'service': 'ai-hit-prediction',
            'version': os.getenv('APP_VERSION', '1.0.0')
        }
        context.update(extra)
        return context
    
    def debug(self, message: str, **kwargs):
        """デバッグログ"""
        self.logger.debug(message, extra=self._add_context(kwargs))
    
    def info(self, message: str, **kwargs):
        """情報ログ"""
        self.logger.info(message, extra=self._add_context(kwargs))
    
    def warning(self, message: str, **kwargs):
        """警告ログ"""
        self.logger.warning(message, extra=self._add_context(kwargs))
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """エラーログ"""
        extra = self._add_context(kwargs)
        if error:
            extra['error_type'] = type(error).__name__
            extra['error_message'] = str(error)
            extra['stacktrace'] = traceback.format_exc()
            
            # Sentryに送信
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(error)
        
        self.logger.error(message, extra=extra)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """クリティカルログ"""
        extra = self._add_context(kwargs)
        if error:
            extra['error_type'] = type(error).__name__
            extra['error_message'] = str(error)
            extra['stacktrace'] = traceback.format_exc()
            
            # Sentryに送信
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(error)
        
        self.logger.critical(message, extra=extra)
    
    def log_request(self, method: str, path: str, status: int, 
                    duration: float, **kwargs):
        """HTTPリクエストログ"""
        self.info(
            f"{method} {path} {status}",
            method=method,
            path=path,
            status=status,
            duration=duration,
            **kwargs
        )
    
    def log_prediction(self, model_type: str, input_data: Dict,
                      prediction: Any, confidence: float, duration: float):
        """予測ログ"""
        self.info(
            "Prediction completed",
            model_type=model_type,
            input_features=len(input_data),
            prediction=prediction,
            confidence=confidence,
            duration=duration
        )
    
    def log_performance(self, operation: str, duration: float, 
                       success: bool, **kwargs):
        """パフォーマンスログ"""
        level = 'info' if success else 'warning'
        getattr(self, level)(
            f"Operation: {operation}",
            operation=operation,
            duration=duration,
            success=success,
            **kwargs
        )


class AuditLogger:
    """監査ログクラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = StructuredLogger("audit", "INFO")
    
    def log_access(self, user_id: str, resource: str, action: str,
                   result: str, ip_address: Optional[str] = None):
        """アクセスログ"""
        self.logger.info(
            "Resource access",
            user_id=user_id,
            resource=resource,
            action=action,
            result=result,
            ip_address=ip_address,
            log_type="access"
        )
    
    def log_data_change(self, user_id: str, entity: str, entity_id: str,
                        action: str, old_value: Any, new_value: Any):
        """データ変更ログ"""
        self.logger.info(
            "Data change",
            user_id=user_id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            log_type="data_change"
        )
    
    def log_authentication(self, user_id: str, action: str, 
                          success: bool, method: str, 
                          ip_address: Optional[str] = None):
        """認証ログ"""
        level = 'info' if success else 'warning'
        getattr(self.logger, level)(
            "Authentication event",
            user_id=user_id,
            action=action,
            success=success,
            method=method,
            ip_address=ip_address,
            log_type="authentication"
        )
    
    def log_security_event(self, event_type: str, severity: str,
                          details: Dict[str, Any]):
        """セキュリティイベントログ"""
        level = 'critical' if severity == 'high' else 'warning'
        getattr(self.logger, level)(
            f"Security event: {event_type}",
            event_type=event_type,
            severity=severity,
            details=details,
            log_type="security"
        )


class PerformanceMonitor:
    """パフォーマンス監視クラス"""
    
    def __init__(self):
        """初期化"""
        self.logger = StructuredLogger("performance", "INFO")
        self.metrics = MetricsCollector()
        self.thresholds = {
            'api_response_time': 1.0,  # 1秒
            'prediction_time': 2.0,    # 2秒
            'batch_processing_time': 10.0,  # 10秒
            'memory_usage_percent': 80,  # 80%
            'cpu_usage_percent': 70  # 70%
        }
    
    def monitor_response_time(self, endpoint: str, duration: float):
        """レスポンスタイム監視"""
        if duration > self.thresholds['api_response_time']:
            self.logger.warning(
                f"Slow response detected",
                endpoint=endpoint,
                duration=duration,
                threshold=self.thresholds['api_response_time']
            )
    
    def monitor_prediction_time(self, model_type: str, duration: float):
        """予測時間監視"""
        if duration > self.thresholds['prediction_time']:
            self.logger.warning(
                f"Slow prediction detected",
                model_type=model_type,
                duration=duration,
                threshold=self.thresholds['prediction_time']
            )
    
    def monitor_system_resources(self):
        """システムリソース監視"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.thresholds['cpu_usage_percent']:
                self.logger.warning(
                    "High CPU usage detected",
                    cpu_percent=cpu_percent,
                    threshold=self.thresholds['cpu_usage_percent']
                )
            
            # メモリ使用率
            memory = psutil.virtual_memory()
            if memory.percent > self.thresholds['memory_usage_percent']:
                self.logger.warning(
                    "High memory usage detected",
                    memory_percent=memory.percent,
                    memory_available_gb=memory.available / (1024**3),
                    threshold=self.thresholds['memory_usage_percent']
                )
            
            # ディスク使用率
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                self.logger.critical(
                    "Critical disk usage",
                    disk_percent=disk.percent,
                    disk_free_gb=disk.free / (1024**3)
                )
            
        except ImportError:
            pass
    
    def monitor_model_performance(self, model_type: str, metrics: Dict[str, float]):
        """モデルパフォーマンス監視"""
        # 精度の閾値チェック
        if metrics.get('accuracy', 1.0) < 0.7:
            self.logger.warning(
                "Model accuracy below threshold",
                model_type=model_type,
                accuracy=metrics.get('accuracy'),
                threshold=0.7
            )
        
        # メトリクス記録
        if PROMETHEUS_AVAILABLE:
            self.metrics.set_model_accuracy(model_type, metrics.get('accuracy', 0))


# グローバルインスタンス
logger = StructuredLogger("ai-hit-prediction")
audit_logger = AuditLogger()
performance_monitor = PerformanceMonitor()
metrics_collector = MetricsCollector()

# コンテキストマネージャー
class LogContext:
    """ログコンテキストマネージャー"""
    
    def __init__(self, operation: str, **kwargs):
        self.operation = operation
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.utcnow()
        logger.info(f"Starting {self.operation}", **self.kwargs)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.utcnow() - self.start_time).total_seconds()
        
        if exc_type is None:
            logger.info(
                f"Completed {self.operation}",
                duration=duration,
                success=True,
                **self.kwargs
            )
        else:
            logger.error(
                f"Failed {self.operation}",
                duration=duration,
                success=False,
                error=exc_val,
                **self.kwargs
            )
        
        return False


# デコレーター
def log_execution(func):
    """実行ログデコレーター"""
    def wrapper(*args, **kwargs):
        with LogContext(f"Function: {func.__name__}"):
            return func(*args, **kwargs)
    return wrapper


def monitor_performance(func):
    """パフォーマンス監視デコレーター"""
    def wrapper(*args, **kwargs):
        start = datetime.utcnow()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.utcnow() - start).total_seconds()
            performance_monitor.logger.info(
                f"Performance: {func.__name__}",
                function=func.__name__,
                duration=duration,
                success=True
            )
            return result
        except Exception as e:
            duration = (datetime.utcnow() - start).total_seconds()
            performance_monitor.logger.error(
                f"Performance: {func.__name__}",
                function=func.__name__,
                duration=duration,
                success=False,
                error=str(e)
            )
            raise
    return wrapper