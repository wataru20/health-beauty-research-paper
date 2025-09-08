import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import re
from collections import Counter
from datetime import datetime, timedelta

class SNSIntegratedAnalyzer:
    """SNSデータ統合分析システム"""
    
    def __init__(self):
        self.buzz_keywords = {
            'korea': ['韓国', 'K-Beauty', 'オルチャン', 'ソウル', '韓国コスメ'],
            'trending': ['バズ', 'ヤバい', '最強', '神', '推し'],
            'effect': ['美白', '保湿', 'ツヤ', 'もちもち', 'しっとり'],
            'problem': ['ニキビ', '毛穴', 'シミ', 'くすみ', '乾燥']
        }
        
        self.platform_weights = {
            'youtube': 0.25,
            'instagram': 0.30,
            'tiktok': 0.35,
            'twitter': 0.10
        }
    
    def analyze_youtube_trends(self, youtube_data: pd.DataFrame) -> Dict:
        """YouTube動画トレンド分析"""
        
        # エンゲージメント率計算
        youtube_data['engagement_rate'] = (
            (youtube_data['likes'] + youtube_data['comments_count']) / 
            youtube_data['views'] * 100
        )
        
        # 急上昇判定（過去7日間で視聴回数が3倍以上）
        youtube_data['is_trending'] = youtube_data['views'] > youtube_data['views'].median() * 3
        
        # キーワード抽出
        all_titles = ' '.join(youtube_data['title'].dropna())
        keywords = self._extract_keywords(all_titles)
        
        return {
            'avg_engagement': youtube_data['engagement_rate'].mean(),
            'trending_videos': youtube_data['is_trending'].sum(),
            'top_keywords': keywords[:10],
            'viral_score': self._calculate_viral_score(youtube_data)
        }
    
    def analyze_instagram_engagement(self, instagram_data: pd.DataFrame) -> Dict:
        """Instagram エンゲージメント分析"""
        
        # インフルエンサー分類
        instagram_data['influencer_tier'] = pd.cut(
            instagram_data['followers'],
            bins=[0, 1000, 10000, 100000, 1000000, float('inf')],
            labels=['nano', 'micro', 'mid', 'macro', 'mega']
        )
        
        # ハッシュタグ分析
        all_hashtags = []
        for hashtags in instagram_data['hashtags']:
            if isinstance(hashtags, list):
                all_hashtags.extend(hashtags)
        
        hashtag_trends = Counter(all_hashtags).most_common(20)
        
        # リール vs 通常投稿のパフォーマンス比較
        reel_engagement = instagram_data[instagram_data['post_type'] == 'reel']['engagement_rate'].mean()
        post_engagement = instagram_data[instagram_data['post_type'] == 'post']['engagement_rate'].mean()
        
        return {
            'influencer_distribution': instagram_data['influencer_tier'].value_counts().to_dict(),
            'trending_hashtags': hashtag_trends,
            'reel_performance': reel_engagement,
            'post_performance': post_engagement,
            'optimal_format': 'reel' if reel_engagement > post_engagement else 'post'
        }
    
    def analyze_tiktok_virality(self, tiktok_data: pd.DataFrame) -> Dict:
        """TikTok バイラル性分析"""
        
        # バイラル係数計算
        tiktok_data['viral_coefficient'] = (
            tiktok_data['shares'] / tiktok_data['views'] * 100
        )
        
        # 音源トレンド分析
        music_trends = tiktok_data['music_used'].value_counts().head(10)
        
        # 最適動画長分析
        duration_bins = pd.cut(tiktok_data['duration'], bins=[0, 15, 30, 60, float('inf')])
        duration_performance = tiktok_data.groupby(duration_bins)['likes'].mean()
        
        return {
            'avg_viral_coefficient': tiktok_data['viral_coefficient'].mean(),
            'trending_music': music_trends.to_dict(),
            'optimal_duration': duration_performance.idxmax(),
            'share_rate': (tiktok_data['shares'] / tiktok_data['views'] * 100).mean()
        }
    
    def analyze_sentiment_twitter(self, twitter_data: pd.DataFrame) -> Dict:
        """Twitter センチメント分析"""
        
        sentiment_distribution = twitter_data['sentiment'].value_counts(normalize=True)
        
        # ポジティブ率によるスコアリング
        positive_rate = sentiment_distribution.get('positive', 0)
        negative_rate = sentiment_distribution.get('negative', 0)
        sentiment_score = (positive_rate - negative_rate) * 100
        
        # インフルエンサーツイート検出
        influencer_tweets = twitter_data[twitter_data['retweets'] > twitter_data['retweets'].quantile(0.9)]
        
        return {
            'sentiment_score': sentiment_score,
            'positive_rate': positive_rate,
            'negative_rate': negative_rate,
            'influencer_mentions': len(influencer_tweets),
            'avg_amplification': twitter_data['retweets'].mean()
        }
    
    def extract_trending_keywords(self, text_data: List[str]) -> Dict:
        """トレンドキーワード抽出"""
        
        all_text = ' '.join(text_data)
        
        # 品質ワード検出
        quality_words = {
            'texture': ['さらさら', 'しっとり', 'もちもち', 'ツルツル', 'ふわふわ'],
            'effect': ['即効', '速攻', '一瞬で', 'すぐに', '翌朝'],
            'value': ['コスパ', 'プチプラ', 'お得', 'デパコス級', '高級感']
        }
        
        word_scores = {}
        for category, words in quality_words.items():
            for word in words:
                count = all_text.count(word)
                if count > 0:
                    word_scores[word] = {
                        'category': category,
                        'count': count,
                        'score': count * self._get_word_weight(category)
                    }
        
        return word_scores
    
    def calculate_integrated_score(self, 
                                  youtube_result: Dict,
                                  instagram_result: Dict,
                                  tiktok_result: Dict,
                                  twitter_result: Dict,
                                  sales_correlation: float) -> Dict:
        """統合予測スコア算出"""
        
        # SNSスコア計算
        sns_scores = {
            'youtube': youtube_result.get('viral_score', 0) * self.platform_weights['youtube'],
            'instagram': instagram_result.get('reel_performance', 0) * self.platform_weights['instagram'],
            'tiktok': tiktok_result.get('avg_viral_coefficient', 0) * self.platform_weights['tiktok'],
            'twitter': twitter_result.get('sentiment_score', 0) * self.platform_weights['twitter']
        }
        
        # 統合スコア
        sns_total_score = sum(sns_scores.values())
        
        # 最終予測スコア（SNS:売上相関 = 6:4）
        final_score = sns_total_score * 0.6 + sales_correlation * 0.4
        
        return {
            'final_prediction_score': final_score,
            'sns_contribution': sns_total_score * 0.6,
            'sales_contribution': sales_correlation * 0.4,
            'platform_scores': sns_scores,
            'confidence_level': self._get_confidence_level(final_score),
            'recommendation': self._get_recommendation(final_score)
        }
    
    def _extract_keywords(self, text: str) -> List[Tuple[str, int]]:
        """キーワード抽出"""
        words = re.findall(r'[가-힣]+|[a-zA-Z]+|[ァ-ヴー]+', text)
        word_counts = Counter(words)
        return word_counts.most_common()
    
    def _calculate_viral_score(self, data: pd.DataFrame) -> float:
        """バイラルスコア計算"""
        if len(data) == 0:
            return 0
        
        normalized_views = data['views'] / data['views'].max() if data['views'].max() > 0 else 0
        normalized_engagement = data['engagement_rate'] / 100
        
        return (normalized_views.mean() + normalized_engagement.mean()) * 50
    
    def _get_word_weight(self, category: str) -> float:
        """カテゴリ別重み取得"""
        weights = {
            'texture': 1.2,
            'effect': 1.5,
            'value': 1.0
        }
        return weights.get(category, 1.0)
    
    def _get_confidence_level(self, score: float) -> str:
        """信頼度レベル判定"""
        if score >= 80:
            return "非常に高い"
        elif score >= 60:
            return "高い"
        elif score >= 40:
            return "中程度"
        elif score >= 20:
            return "低い"
        else:
            return "非常に低い"
    
    def _get_recommendation(self, score: float) -> str:
        """推奨アクション"""
        if score >= 70:
            return "即座に日本市場投入を強く推奨"
        elif score >= 50:
            return "インフルエンサーマーケティング後、投入"
        elif score >= 30:
            return "限定テスト販売で市場反応を確認"
        else:
            return "追加のSNS分析とトレンド観察が必要"


def generate_sample_sns_data():
    """サンプルSNSデータ生成"""
    
    # YouTube サンプル
    youtube_df = pd.DataFrame({
        'title': ['韓国スキンケアルーティン', 'CICA化粧品レビュー', '毛穴ケア最強アイテム'],
        'views': [500000, 300000, 450000],
        'likes': [25000, 18000, 30000],
        'comments_count': [3000, 2500, 4000]
    })
    
    # Instagram サンプル
    instagram_df = pd.DataFrame({
        'followers': [50000, 100000, 25000],
        'likes': [5000, 12000, 3000],
        'engagement_rate': [10.0, 12.0, 12.0],
        'post_type': ['reel', 'reel', 'post'],
        'hashtags': [['#韓国コスメ'], ['#CICA'], ['#スキンケア']]
    })
    
    # TikTok サンプル
    tiktok_df = pd.DataFrame({
        'views': [1000000, 800000, 1200000],
        'likes': [100000, 90000, 150000],
        'shares': [20000, 15000, 30000],
        'duration': [15, 30, 20],
        'music_used': ['Trending Song 1', 'Trending Song 2', 'Trending Song 1']
    })
    
    # Twitter サンプル
    twitter_df = pd.DataFrame({
        'text': ['最高のスキンケア', 'CICAクリーム良い', '韓国コスメ大好き'],
        'retweets': [500, 300, 800],
        'likes': [1000, 600, 1500],
        'sentiment': ['positive', 'positive', 'positive']
    })
    
    return youtube_df, instagram_df, tiktok_df, twitter_df


if __name__ == "__main__":
    analyzer = SNSIntegratedAnalyzer()
    
    # サンプルデータで分析実行
    youtube, instagram, tiktok, twitter = generate_sample_sns_data()
    
    youtube_result = analyzer.analyze_youtube_trends(youtube)
    instagram_result = analyzer.analyze_instagram_engagement(instagram)
    tiktok_result = analyzer.analyze_tiktok_virality(tiktok)
    twitter_result = analyzer.analyze_sentiment_twitter(twitter)
    
    # 統合スコア計算
    integrated_result = analyzer.calculate_integrated_score(
        youtube_result, 
        instagram_result,
        tiktok_result,
        twitter_result,
        sales_correlation=0.75
    )
    
    print("SNS統合分析結果")
    print("=" * 50)
    print(f"最終予測スコア: {integrated_result['final_prediction_score']:.2f}")
    print(f"信頼度: {integrated_result['confidence_level']}")
    print(f"推奨アクション: {integrated_result['recommendation']}")