#!/usr/bin/env python
"""
Feedback Collection and Analysis System
フィードバック収集・分析システム
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import uuid
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeedbackType(Enum):
    """フィードバックタイプ"""
    PREDICTION_ACCURACY = "prediction_accuracy"
    USER_EXPERIENCE = "user_experience"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"
    PERFORMANCE = "performance"
    BUSINESS_IMPACT = "business_impact"


class SentimentLevel(Enum):
    """感情レベル"""
    VERY_NEGATIVE = 1
    NEGATIVE = 2
    NEUTRAL = 3
    POSITIVE = 4
    VERY_POSITIVE = 5


@dataclass
class Feedback:
    """フィードバックデータクラス"""
    id: str
    user_id: str
    timestamp: str
    type: FeedbackType
    category: str
    subject: str
    description: str
    sentiment: SentimentLevel
    priority: int  # 1-5
    metadata: Dict[str, Any]
    status: str = "open"
    resolution: Optional[str] = None
    response: Optional[str] = None


class FeedbackCollector:
    """フィードバック収集クラス"""
    
    def __init__(self):
        """初期化"""
        self.feedbacks = []
        self.feedback_db = {}  # 実際はデータベース使用
        
    def submit_feedback(self,
                        user_id: str,
                        type: FeedbackType,
                        subject: str,
                        description: str,
                        category: str = "general",
                        priority: int = 3,
                        metadata: Optional[Dict] = None) -> str:
        """
        フィードバック送信
        
        Args:
            user_id: ユーザーID
            type: フィードバックタイプ
            subject: 件名
            description: 詳細
            category: カテゴリ
            priority: 優先度
            metadata: メタデータ
        
        Returns:
            フィードバックID
        """
        feedback_id = str(uuid.uuid4())
        
        # 感情分析
        sentiment = self._analyze_sentiment(description)
        
        feedback = Feedback(
            id=feedback_id,
            user_id=user_id,
            timestamp=datetime.utcnow().isoformat(),
            type=type,
            category=category,
            subject=subject,
            description=description,
            sentiment=sentiment,
            priority=priority,
            metadata=metadata or {},
            status="open"
        )
        
        # 保存
        self.feedbacks.append(feedback)
        self.feedback_db[feedback_id] = feedback
        
        # 通知送信（高優先度の場合）
        if priority >= 4:
            self._send_urgent_notification(feedback)
        
        logger.info(f"Feedback submitted: {feedback_id}")
        
        return feedback_id
    
    def _analyze_sentiment(self, text: str) -> SentimentLevel:
        """
        感情分析（簡易版）
        
        Args:
            text: 分析するテキスト
        
        Returns:
            感情レベル
        """
        # ポジティブ/ネガティブワード（実際はMLモデル使用）
        positive_words = ['excellent', 'great', 'good', 'amazing', 'helpful', 'useful']
        negative_words = ['bad', 'poor', 'terrible', 'awful', 'useless', 'broken']
        
        text_lower = text.lower()
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        score = positive_count - negative_count
        
        if score >= 2:
            return SentimentLevel.VERY_POSITIVE
        elif score == 1:
            return SentimentLevel.POSITIVE
        elif score == 0:
            return SentimentLevel.NEUTRAL
        elif score == -1:
            return SentimentLevel.NEGATIVE
        else:
            return SentimentLevel.VERY_NEGATIVE
    
    def _send_urgent_notification(self, feedback: Feedback):
        """緊急通知送信"""
        logger.warning(f"Urgent feedback received: {feedback.subject}")
        # Slack/Email通知実装
    
    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """フィードバック取得"""
        return self.feedback_db.get(feedback_id)
    
    def update_feedback_status(self, 
                              feedback_id: str,
                              status: str,
                              resolution: Optional[str] = None,
                              response: Optional[str] = None) -> bool:
        """
        フィードバックステータス更新
        
        Args:
            feedback_id: フィードバックID
            status: 新しいステータス
            resolution: 解決内容
            response: 返信
        
        Returns:
            成功フラグ
        """
        feedback = self.feedback_db.get(feedback_id)
        if not feedback:
            return False
        
        feedback.status = status
        if resolution:
            feedback.resolution = resolution
        if response:
            feedback.response = response
        
        logger.info(f"Feedback {feedback_id} updated to {status}")
        
        return True
    
    def search_feedbacks(self,
                        user_id: Optional[str] = None,
                        type: Optional[FeedbackType] = None,
                        status: Optional[str] = None,
                        start_date: Optional[datetime] = None,
                        end_date: Optional[datetime] = None) -> List[Feedback]:
        """
        フィードバック検索
        
        Args:
            user_id: ユーザーID
            type: タイプ
            status: ステータス
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            フィードバックリスト
        """
        results = self.feedbacks
        
        if user_id:
            results = [f for f in results if f.user_id == user_id]
        
        if type:
            results = [f for f in results if f.type == type]
        
        if status:
            results = [f for f in results if f.status == status]
        
        if start_date:
            results = [f for f in results 
                      if datetime.fromisoformat(f.timestamp) >= start_date]
        
        if end_date:
            results = [f for f in results 
                      if datetime.fromisoformat(f.timestamp) <= end_date]
        
        return results


class FeedbackAnalyzer:
    """フィードバック分析クラス"""
    
    def __init__(self, collector: FeedbackCollector):
        """初期化"""
        self.collector = collector
    
    def generate_summary(self, period_days: int = 30) -> Dict[str, Any]:
        """
        フィードバックサマリー生成
        
        Args:
            period_days: 集計期間（日数）
        
        Returns:
            サマリー
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        feedbacks = self.collector.search_feedbacks(
            start_date=start_date,
            end_date=end_date
        )
        
        if not feedbacks:
            return {
                'period_days': period_days,
                'total_feedbacks': 0,
                'message': 'No feedbacks in this period'
            }
        
        # 集計
        summary = {
            'period_days': period_days,
            'total_feedbacks': len(feedbacks),
            'by_type': {},
            'by_sentiment': {},
            'by_status': {},
            'average_priority': 0,
            'resolution_rate': 0,
            'top_issues': [],
            'trends': []
        }
        
        # タイプ別集計
        for fb_type in FeedbackType:
            count = sum(1 for f in feedbacks if f.type == fb_type)
            if count > 0:
                summary['by_type'][fb_type.value] = count
        
        # 感情別集計
        for sentiment in SentimentLevel:
            count = sum(1 for f in feedbacks if f.sentiment == sentiment)
            if count > 0:
                summary['by_sentiment'][sentiment.name] = count
        
        # ステータス別集計
        statuses = set(f.status for f in feedbacks)
        for status in statuses:
            count = sum(1 for f in feedbacks if f.status == status)
            summary['by_status'][status] = count
        
        # 平均優先度
        priorities = [f.priority for f in feedbacks]
        summary['average_priority'] = np.mean(priorities)
        
        # 解決率
        resolved = sum(1 for f in feedbacks if f.status == 'resolved')
        summary['resolution_rate'] = resolved / len(feedbacks)
        
        # トップ課題
        summary['top_issues'] = self._identify_top_issues(feedbacks)
        
        # トレンド分析
        summary['trends'] = self._analyze_trends(feedbacks)
        
        return summary
    
    def _identify_top_issues(self, feedbacks: List[Feedback], top_n: int = 5) -> List[Dict]:
        """
        主要な課題を特定
        
        Args:
            feedbacks: フィードバックリスト
            top_n: 上位N件
        
        Returns:
            課題リスト
        """
        # 優先度と感情スコアで課題をスコアリング
        issues = []
        
        for feedback in feedbacks:
            if feedback.sentiment.value <= 2:  # ネガティブなフィードバック
                score = feedback.priority * (3 - feedback.sentiment.value)
                issues.append({
                    'subject': feedback.subject,
                    'type': feedback.type.value,
                    'count': 1,  # 実際は類似課題をグループ化
                    'score': score
                })
        
        # スコアでソート
        issues.sort(key=lambda x: x['score'], reverse=True)
        
        return issues[:top_n]
    
    def _analyze_trends(self, feedbacks: List[Feedback]) -> List[Dict]:
        """
        トレンド分析
        
        Args:
            feedbacks: フィードバックリスト
        
        Returns:
            トレンドリスト
        """
        if len(feedbacks) < 2:
            return []
        
        # 日別集計
        df = pd.DataFrame([asdict(f) for f in feedbacks])
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
        
        daily_counts = df.groupby('date').size()
        
        # トレンド検出（簡易版）
        trends = []
        
        if len(daily_counts) >= 7:
            # 移動平均
            ma7 = daily_counts.rolling(window=7).mean()
            
            # 上昇/下降トレンド
            if ma7.iloc[-1] > ma7.iloc[-7] * 1.2:
                trends.append({
                    'type': 'increasing',
                    'metric': 'feedback_volume',
                    'change': float((ma7.iloc[-1] / ma7.iloc[-7] - 1) * 100)
                })
            elif ma7.iloc[-1] < ma7.iloc[-7] * 0.8:
                trends.append({
                    'type': 'decreasing',
                    'metric': 'feedback_volume',
                    'change': float((ma7.iloc[-1] / ma7.iloc[-7] - 1) * 100)
                })
        
        return trends
    
    def generate_action_items(self, feedbacks: List[Feedback]) -> List[Dict]:
        """
        アクションアイテム生成
        
        Args:
            feedbacks: フィードバックリスト
        
        Returns:
            アクションアイテムリスト
        """
        action_items = []
        
        # バグ報告の処理
        bugs = [f for f in feedbacks 
                if f.type == FeedbackType.BUG_REPORT and f.status == 'open']
        
        for bug in bugs:
            action_items.append({
                'type': 'bug_fix',
                'priority': bug.priority,
                'description': f"Fix: {bug.subject}",
                'feedback_id': bug.id
            })
        
        # 機能リクエストの集約
        feature_requests = [f for f in feedbacks 
                           if f.type == FeedbackType.FEATURE_REQUEST]
        
        if len(feature_requests) >= 3:  # 複数のリクエストがある場合
            action_items.append({
                'type': 'feature_development',
                'priority': 3,
                'description': f"Evaluate {len(feature_requests)} feature requests",
                'feedback_ids': [f.id for f in feature_requests]
            })
        
        # パフォーマンス問題
        perf_issues = [f for f in feedbacks 
                      if f.type == FeedbackType.PERFORMANCE and f.priority >= 4]
        
        if perf_issues:
            action_items.append({
                'type': 'performance_optimization',
                'priority': 5,
                'description': "Urgent: Address performance issues",
                'feedback_ids': [f.id for f in perf_issues]
            })
        
        # 優先度でソート
        action_items.sort(key=lambda x: x['priority'], reverse=True)
        
        return action_items


class PredictionFeedbackTracker:
    """予測精度フィードバックトラッカー"""
    
    def __init__(self):
        """初期化"""
        self.predictions = {}
        self.actual_results = {}
    
    def record_prediction(self,
                         product_id: str,
                         prediction_id: str,
                         hit_probability: float,
                         timestamp: datetime):
        """
        予測記録
        
        Args:
            product_id: 製品ID
            prediction_id: 予測ID
            hit_probability: ヒット確率
            timestamp: タイムスタンプ
        """
        self.predictions[prediction_id] = {
            'product_id': product_id,
            'hit_probability': hit_probability,
            'timestamp': timestamp.isoformat(),
            'actual_result': None,
            'feedback_received': False
        }
    
    def record_actual_result(self,
                           prediction_id: str,
                           actual_hit: bool,
                           sales_data: Optional[Dict] = None):
        """
        実際の結果記録
        
        Args:
            prediction_id: 予測ID
            actual_hit: 実際のヒット有無
            sales_data: 売上データ
        """
        if prediction_id in self.predictions:
            self.predictions[prediction_id]['actual_result'] = actual_hit
            self.predictions[prediction_id]['sales_data'] = sales_data
            self.predictions[prediction_id]['feedback_received'] = True
            
            # 精度計算
            predicted_hit = self.predictions[prediction_id]['hit_probability'] > 0.5
            correct = predicted_hit == actual_hit
            
            logger.info(f"Prediction {prediction_id}: "
                       f"Predicted={predicted_hit}, Actual={actual_hit}, "
                       f"Correct={correct}")
    
    def calculate_accuracy_metrics(self, 
                                  start_date: Optional[datetime] = None,
                                  end_date: Optional[datetime] = None) -> Dict:
        """
        精度メトリクス計算
        
        Args:
            start_date: 開始日
            end_date: 終了日
        
        Returns:
            精度メトリクス
        """
        # フィードバックのある予測を抽出
        evaluated = [p for p in self.predictions.values() 
                    if p['feedback_received']]
        
        if not evaluated:
            return {'message': 'No evaluated predictions'}
        
        # 期間フィルタ
        if start_date:
            evaluated = [p for p in evaluated 
                        if datetime.fromisoformat(p['timestamp']) >= start_date]
        
        if end_date:
            evaluated = [p for p in evaluated 
                        if datetime.fromisoformat(p['timestamp']) <= end_date]
        
        # 精度計算
        correct = 0
        true_positives = 0
        true_negatives = 0
        false_positives = 0
        false_negatives = 0
        
        for pred in evaluated:
            predicted_hit = pred['hit_probability'] > 0.5
            actual_hit = pred['actual_result']
            
            if predicted_hit == actual_hit:
                correct += 1
                if actual_hit:
                    true_positives += 1
                else:
                    true_negatives += 1
            else:
                if predicted_hit:
                    false_positives += 1
                else:
                    false_negatives += 1
        
        total = len(evaluated)
        
        # メトリクス計算
        accuracy = correct / total if total > 0 else 0
        precision = true_positives / (true_positives + false_positives) \
                   if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) \
                if (true_positives + false_negatives) > 0 else 0
        f1 = 2 * (precision * recall) / (precision + recall) \
            if (precision + recall) > 0 else 0
        
        return {
            'total_predictions': total,
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': {
                'true_positives': true_positives,
                'true_negatives': true_negatives,
                'false_positives': false_positives,
                'false_negatives': false_negatives
            }
        }


# グローバルインスタンス
feedback_collector = FeedbackCollector()
feedback_analyzer = FeedbackAnalyzer(feedback_collector)
prediction_tracker = PredictionFeedbackTracker()