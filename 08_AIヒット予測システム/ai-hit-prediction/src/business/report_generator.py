#!/usr/bin/env python
"""
Business Report Generator Module
ビジネスレポート自動生成機能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from pathlib import Path
import logging

# レポート生成ライブラリ
from jinja2 import Template, Environment, FileSystemLoader
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# PDFとExcel出力
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("ReportLab not available. PDF export disabled.")

import xlsxwriter

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """レポート生成クラス"""
    
    def __init__(self, template_dir: Optional[str] = None):
        """
        初期化
        
        Args:
            template_dir: テンプレートディレクトリ
        """
        self.template_dir = template_dir or "templates"
        self.styles = getSampleStyleSheet() if REPORTLAB_AVAILABLE else None
        self.report_data = {}
        self.charts = {}
    
    def generate_executive_summary(self, 
                                  predictions: pd.DataFrame,
                                  market_trends: Dict[str, Any],
                                  period: str = "monthly") -> Dict[str, Any]:
        """
        エグゼクティブサマリー生成
        
        Args:
            predictions: 予測結果データ
            market_trends: 市場トレンドデータ
            period: 期間（monthly, weekly, quarterly）
        
        Returns:
            サマリーデータ
        """
        summary = {
            'report_date': datetime.now().strftime('%Y年%m月%d日'),
            'period': period,
            'key_metrics': {},
            'insights': [],
            'recommendations': []
        }
        
        # 主要メトリクス計算
        if not predictions.empty:
            summary['key_metrics'] = {
                'total_products_analyzed': len(predictions),
                'high_potential_products': len(predictions[predictions['hit_probability'] > 0.7]),
                'average_hit_probability': predictions['hit_probability'].mean(),
                'success_rate': (predictions['hit_probability'] > 0.5).mean(),
                'risk_distribution': {
                    'low': len(predictions[predictions['risk_level'] == '低']),
                    'medium': len(predictions[predictions['risk_level'] == '中']),
                    'high': len(predictions[predictions['risk_level'] == '高'])
                }
            }
        
        # インサイト生成
        insights = self._generate_insights(predictions, market_trends)
        summary['insights'] = insights
        
        # 推奨事項生成
        recommendations = self._generate_recommendations(predictions, market_trends)
        summary['recommendations'] = recommendations
        
        # トレンドハイライト
        if market_trends:
            summary['trend_highlights'] = {
                'top_categories': self._get_top_categories(market_trends),
                'emerging_ingredients': self._get_emerging_ingredients(market_trends),
                'price_trends': self._analyze_price_trends(predictions)
            }
        
        self.report_data['executive_summary'] = summary
        return summary
    
    def generate_market_analysis_report(self,
                                       market_data: pd.DataFrame,
                                       competitor_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        市場分析レポート生成
        
        Args:
            market_data: 市場データ
            competitor_data: 競合データ
        
        Returns:
            市場分析レポート
        """
        analysis = {
            'market_overview': {},
            'category_performance': {},
            'competitive_landscape': {},
            'opportunity_analysis': {}
        }
        
        # 市場概要
        if not market_data.empty:
            analysis['market_overview'] = {
                'total_market_size': self._estimate_market_size(market_data),
                'growth_rate': self._calculate_growth_rate(market_data),
                'market_segments': self._analyze_segments(market_data),
                'seasonality': self._detect_seasonality(market_data)
            }
        
        # カテゴリ別パフォーマンス
        if 'category' in market_data.columns:
            category_perf = market_data.groupby('category').agg({
                'trend_score': 'mean',
                'buzz_score': 'mean'
            }).to_dict('index')
            analysis['category_performance'] = category_perf
        
        # 競合分析
        if competitor_data is not None and not competitor_data.empty:
            analysis['competitive_landscape'] = {
                'market_share': self._analyze_market_share(competitor_data),
                'competitive_positioning': self._analyze_positioning(competitor_data),
                'competitor_strengths': self._identify_strengths(competitor_data)
            }
        
        # 機会分析
        analysis['opportunity_analysis'] = {
            'untapped_segments': self._identify_opportunities(market_data),
            'growth_areas': self._identify_growth_areas(market_data),
            'risk_factors': self._identify_risks(market_data)
        }
        
        self.report_data['market_analysis'] = analysis
        return analysis
    
    def generate_product_performance_report(self,
                                           products: pd.DataFrame,
                                           historical_data: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """
        製品パフォーマンスレポート生成
        
        Args:
            products: 製品データ
            historical_data: 履歴データ
        
        Returns:
            製品パフォーマンスレポート
        """
        performance = {
            'top_performers': [],
            'underperformers': [],
            'performance_metrics': {},
            'improvement_areas': []
        }
        
        if not products.empty:
            # トップパフォーマー
            top_products = products.nlargest(10, 'hit_probability')
            performance['top_performers'] = top_products[['name', 'hit_probability', 'confidence']].to_dict('records')
            
            # アンダーパフォーマー
            bottom_products = products.nsmallest(10, 'hit_probability')
            performance['underperformers'] = bottom_products[['name', 'hit_probability', 'risk_level']].to_dict('records')
            
            # パフォーマンスメトリクス
            performance['performance_metrics'] = {
                'avg_performance': products['hit_probability'].mean(),
                'performance_std': products['hit_probability'].std(),
                'confidence_avg': products['confidence'].mean() if 'confidence' in products else None
            }
            
            # 改善エリア特定
            if 'factors' in products.columns:
                improvement_areas = self._identify_improvement_areas(products)
                performance['improvement_areas'] = improvement_areas
        
        # 履歴トレンド分析
        if historical_data is not None and not historical_data.empty:
            performance['historical_trends'] = self._analyze_historical_trends(historical_data)
        
        self.report_data['product_performance'] = performance
        return performance
    
    def create_visualization_charts(self, data: Dict[str, Any]) -> Dict[str, go.Figure]:
        """
        ビジュアライゼーションチャート作成
        
        Args:
            data: レポートデータ
        
        Returns:
            チャート辞書
        """
        charts = {}
        
        # 1. ヒット確率分布
        if 'predictions' in data:
            charts['hit_probability_dist'] = self._create_probability_distribution(data['predictions'])
        
        # 2. カテゴリ別パフォーマンス
        if 'category_performance' in data:
            charts['category_performance'] = self._create_category_chart(data['category_performance'])
        
        # 3. トレンド推移
        if 'market_trends' in data:
            charts['trend_evolution'] = self._create_trend_chart(data['market_trends'])
        
        # 4. リスク分析マトリックス
        if 'predictions' in data:
            charts['risk_matrix'] = self._create_risk_matrix(data['predictions'])
        
        # 5. 競合比較
        if 'competitor_data' in data:
            charts['competitor_comparison'] = self._create_competitor_chart(data['competitor_data'])
        
        self.charts = charts
        return charts
    
    def export_to_pdf(self, filename: str, include_charts: bool = True):
        """
        PDFエクスポート
        
        Args:
            filename: 出力ファイル名
            include_charts: チャートを含むか
        """
        if not REPORTLAB_AVAILABLE:
            logger.error("ReportLab not available. Cannot export to PDF.")
            return
        
        doc = SimpleDocTemplate(filename, pagesize=A4)
        story = []
        
        # タイトルページ
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1f77b4'),
            spaceAfter=30
        )
        
        title = Paragraph("AI化粧品ヒット予測システム<br/>ビジネスレポート", title_style)
        story.append(title)
        story.append(Spacer(1, 0.5*inch))
        
        # 日付
        date_text = f"作成日: {datetime.now().strftime('%Y年%m月%d日')}"
        story.append(Paragraph(date_text, self.styles['Normal']))
        story.append(PageBreak())
        
        # エグゼクティブサマリー
        if 'executive_summary' in self.report_data:
            story.extend(self._create_summary_section())
            story.append(PageBreak())
        
        # 市場分析
        if 'market_analysis' in self.report_data:
            story.extend(self._create_market_section())
            story.append(PageBreak())
        
        # 製品パフォーマンス
        if 'product_performance' in self.report_data:
            story.extend(self._create_performance_section())
        
        # PDF生成
        doc.build(story)
        logger.info(f"PDF report generated: {filename}")
    
    def export_to_excel(self, filename: str):
        """
        Excelエクスポート
        
        Args:
            filename: 出力ファイル名
        """
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # フォーマット定義
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#1f77b4',
                'font_color': 'white',
                'border': 1
            })
            
            # サマリーシート
            if 'executive_summary' in self.report_data:
                summary_df = pd.DataFrame([self.report_data['executive_summary']['key_metrics']])
                summary_df.to_excel(writer, sheet_name='エグゼクティブサマリー', index=False)
                
                worksheet = writer.sheets['エグゼクティブサマリー']
                for col_num, value in enumerate(summary_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
            
            # 予測結果シート
            if 'predictions' in self.report_data:
                self.report_data['predictions'].to_excel(writer, sheet_name='予測結果', index=False)
            
            # 市場分析シート
            if 'market_analysis' in self.report_data:
                market_df = pd.DataFrame(self.report_data['market_analysis']['category_performance']).T
                market_df.to_excel(writer, sheet_name='市場分析')
            
            # チャート追加（可能な場合）
            if self.charts:
                chart_sheet = workbook.add_worksheet('チャート')
                chart_sheet.write(0, 0, 'チャートは別途提供されます')
        
        logger.info(f"Excel report generated: {filename}")
    
    def export_to_html(self, filename: str, template: Optional[str] = None):
        """
        HTMLエクスポート
        
        Args:
            filename: 出力ファイル名
            template: HTMLテンプレート
        """
        if template:
            env = Environment(loader=FileSystemLoader(self.template_dir))
            html_template = env.get_template(template)
        else:
            # デフォルトテンプレート
            html_template = Template("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>AI Hit Prediction Report</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    h1 { color: #1f77b4; }
                    h2 { color: #333; border-bottom: 2px solid #1f77b4; }
                    .metric { display: inline-block; margin: 10px; padding: 10px; 
                             background: #f0f0f0; border-radius: 5px; }
                    .chart { margin: 20px 0; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #1f77b4; color: white; }
                </style>
            </head>
            <body>
                <h1>AIヒット予測システム ビジネスレポート</h1>
                <p>作成日: {{ report_date }}</p>
                
                <h2>エグゼクティブサマリー</h2>
                {% if executive_summary %}
                <div class="metrics">
                    {% for key, value in executive_summary.key_metrics.items() %}
                    <div class="metric">
                        <strong>{{ key }}:</strong> {{ value }}
                    </div>
                    {% endfor %}
                </div>
                
                <h3>主要インサイト</h3>
                <ul>
                    {% for insight in executive_summary.insights %}
                    <li>{{ insight }}</li>
                    {% endfor %}
                </ul>
                
                <h3>推奨事項</h3>
                <ul>
                    {% for rec in executive_summary.recommendations %}
                    <li>{{ rec }}</li>
                    {% endfor %}
                </ul>
                {% endif %}
                
                {% if charts %}
                <h2>ビジュアライゼーション</h2>
                <div class="charts">
                    <!-- チャートはJavaScriptで動的に生成 -->
                </div>
                {% endif %}
            </body>
            </html>
            """)
        
        # データをHTMLに挿入
        html_content = html_template.render(
            report_date=datetime.now().strftime('%Y年%m月%d日'),
            executive_summary=self.report_data.get('executive_summary'),
            charts=bool(self.charts)
        )
        
        # ファイル保存
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"HTML report generated: {filename}")
    
    # ヘルパーメソッド
    def _generate_insights(self, predictions: pd.DataFrame, trends: Dict) -> List[str]:
        """インサイト生成"""
        insights = []
        
        if not predictions.empty:
            # ヒット確率の分析
            high_potential = (predictions['hit_probability'] > 0.7).sum()
            if high_potential > len(predictions) * 0.3:
                insights.append(f"高いヒットポテンシャルを持つ製品が{high_potential}個検出されました")
            
            # リスク分析
            high_risk = (predictions['risk_level'] == '高').sum()
            if high_risk > len(predictions) * 0.4:
                insights.append("リスクの高い製品が多く、慎重な戦略が必要です")
        
        if trends:
            # トレンド分析
            if 'emerging_keywords' in trends:
                insights.append(f"新興トレンドキーワード: {', '.join(trends['emerging_keywords'][:3])}")
        
        return insights
    
    def _generate_recommendations(self, predictions: pd.DataFrame, trends: Dict) -> List[str]:
        """推奨事項生成"""
        recommendations = []
        
        if not predictions.empty:
            avg_hit_prob = predictions['hit_probability'].mean()
            
            if avg_hit_prob > 0.6:
                recommendations.append("積極的な新製品投入を推奨")
            elif avg_hit_prob > 0.4:
                recommendations.append("選択的な製品投入とテストマーケティングを推奨")
            else:
                recommendations.append("製品戦略の見直しと差別化強化を推奨")
        
        if trends and 'growth_rate' in trends:
            if trends['growth_rate'] > 0.1:
                recommendations.append("市場成長に合わせた生産能力拡大を検討")
        
        return recommendations
    
    def _get_top_categories(self, trends: Dict) -> List[str]:
        """トップカテゴリ取得"""
        if 'categories' in trends:
            return sorted(trends['categories'], 
                         key=lambda x: trends['categories'][x], 
                         reverse=True)[:3]
        return []
    
    def _get_emerging_ingredients(self, trends: Dict) -> List[str]:
        """新興成分取得"""
        return trends.get('emerging_ingredients', [])
    
    def _analyze_price_trends(self, predictions: pd.DataFrame) -> Dict:
        """価格トレンド分析"""
        if 'price' not in predictions.columns:
            return {}
        
        return {
            'average_price': predictions['price'].mean(),
            'price_range': [predictions['price'].min(), predictions['price'].max()],
            'optimal_price_range': self._calculate_optimal_price(predictions)
        }
    
    def _calculate_optimal_price(self, predictions: pd.DataFrame) -> List[float]:
        """最適価格帯計算"""
        if 'price' in predictions.columns and 'hit_probability' in predictions.columns:
            high_perf = predictions[predictions['hit_probability'] > 0.6]
            if not high_perf.empty:
                return [high_perf['price'].quantile(0.25), high_perf['price'].quantile(0.75)]
        return [0, 0]
    
    def _estimate_market_size(self, market_data: pd.DataFrame) -> float:
        """市場規模推定"""
        # 簡易推定ロジック
        return len(market_data) * 1000000  # ダミー値
    
    def _calculate_growth_rate(self, market_data: pd.DataFrame) -> float:
        """成長率計算"""
        if 'trend_score' in market_data.columns:
            return market_data['trend_score'].pct_change().mean()
        return 0.0
    
    def _analyze_segments(self, market_data: pd.DataFrame) -> Dict:
        """セグメント分析"""
        segments = {}
        if 'category' in market_data.columns:
            for category in market_data['category'].unique():
                segment_data = market_data[market_data['category'] == category]
                segments[category] = {
                    'size': len(segment_data),
                    'growth': segment_data['trend_score'].mean() if 'trend_score' in segment_data else 0
                }
        return segments
    
    def _detect_seasonality(self, market_data: pd.DataFrame) -> Dict:
        """季節性検出"""
        # 簡易的な季節性分析
        return {'has_seasonality': False, 'peak_season': 'N/A'}
    
    def _analyze_market_share(self, competitor_data: pd.DataFrame) -> Dict:
        """市場シェア分析"""
        if 'market_share' in competitor_data.columns:
            return competitor_data.set_index('brand')['market_share'].to_dict()
        return {}
    
    def _analyze_positioning(self, competitor_data: pd.DataFrame) -> Dict:
        """ポジショニング分析"""
        return {'positioning_map': 'Generated separately'}
    
    def _identify_strengths(self, competitor_data: pd.DataFrame) -> List[str]:
        """強み特定"""
        return ['ブランド力', '革新性', '価格競争力']
    
    def _identify_opportunities(self, market_data: pd.DataFrame) -> List[str]:
        """機会特定"""
        return ['新規セグメント', '未開拓地域', 'デジタルチャネル']
    
    def _identify_growth_areas(self, market_data: pd.DataFrame) -> List[str]:
        """成長分野特定"""
        return ['オーガニック製品', 'メンズコスメ', 'エイジングケア']
    
    def _identify_risks(self, market_data: pd.DataFrame) -> List[str]:
        """リスク特定"""
        return ['市場飽和', '規制強化', '原材料価格上昇']
    
    def _identify_improvement_areas(self, products: pd.DataFrame) -> List[str]:
        """改善エリア特定"""
        return ['パッケージデザイン', '成分配合', 'マーケティング戦略']
    
    def _analyze_historical_trends(self, historical_data: pd.DataFrame) -> Dict:
        """履歴トレンド分析"""
        return {'trend': 'upward', 'volatility': 'low'}
    
    # PDF用セクション作成メソッド
    def _create_summary_section(self) -> List:
        """サマリーセクション作成"""
        story = []
        story.append(Paragraph("エグゼクティブサマリー", self.styles['Heading1']))
        
        summary = self.report_data['executive_summary']
        
        # メトリクステーブル
        metrics_data = [['指標', '値']]
        for key, value in summary['key_metrics'].items():
            metrics_data.append([key, str(value)])
        
        metrics_table = Table(metrics_data)
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 0.2*inch))
        
        return story
    
    def _create_market_section(self) -> List:
        """市場分析セクション作成"""
        story = []
        story.append(Paragraph("市場分析", self.styles['Heading1']))
        
        # 市場概要
        market = self.report_data['market_analysis']
        overview_text = f"""
        市場規模: {market['market_overview'].get('total_market_size', 'N/A')}<br/>
        成長率: {market['market_overview'].get('growth_rate', 'N/A')}<br/>
        """
        story.append(Paragraph(overview_text, self.styles['Normal']))
        
        return story
    
    def _create_performance_section(self) -> List:
        """パフォーマンスセクション作成"""
        story = []
        story.append(Paragraph("製品パフォーマンス", self.styles['Heading1']))
        
        perf = self.report_data['product_performance']
        
        # トップパフォーマー
        if perf['top_performers']:
            story.append(Paragraph("トップパフォーマー", self.styles['Heading2']))
            top_data = [['製品名', 'ヒット確率']]
            for product in perf['top_performers'][:5]:
                top_data.append([product['name'], f"{product['hit_probability']:.2%}"])
            
            top_table = Table(top_data)
            story.append(top_table)
        
        return story
    
    # チャート作成メソッド
    def _create_probability_distribution(self, predictions: pd.DataFrame) -> go.Figure:
        """確率分布チャート作成"""
        fig = go.Figure(data=[
            go.Histogram(x=predictions['hit_probability'], nbinsx=20)
        ])
        fig.update_layout(
            title="ヒット確率分布",
            xaxis_title="ヒット確率",
            yaxis_title="製品数"
        )
        return fig
    
    def _create_category_chart(self, category_data: Dict) -> go.Figure:
        """カテゴリチャート作成"""
        categories = list(category_data.keys())
        scores = [data['trend_score'] for data in category_data.values()]
        
        fig = go.Figure(data=[
            go.Bar(x=categories, y=scores)
        ])
        fig.update_layout(
            title="カテゴリ別パフォーマンス",
            xaxis_title="カテゴリ",
            yaxis_title="トレンドスコア"
        )
        return fig
    
    def _create_trend_chart(self, trends: pd.DataFrame) -> go.Figure:
        """トレンドチャート作成"""
        fig = go.Figure()
        
        if 'date' in trends.columns and 'trend_score' in trends.columns:
            fig.add_trace(go.Scatter(
                x=trends['date'],
                y=trends['trend_score'],
                mode='lines',
                name='トレンドスコア'
            ))
        
        fig.update_layout(
            title="市場トレンド推移",
            xaxis_title="日付",
            yaxis_title="スコア"
        )
        return fig
    
    def _create_risk_matrix(self, predictions: pd.DataFrame) -> go.Figure:
        """リスクマトリックス作成"""
        fig = go.Figure(data=[
            go.Scatter(
                x=predictions['hit_probability'],
                y=predictions['confidence'] if 'confidence' in predictions else predictions['hit_probability'],
                mode='markers',
                text=predictions['name'] if 'name' in predictions else None,
                marker=dict(
                    size=10,
                    color=predictions['hit_probability'],
                    colorscale='RdYlGn',
                    showscale=True
                )
            )
        ])
        
        fig.update_layout(
            title="リスク・リターンマトリックス",
            xaxis_title="ヒット確率",
            yaxis_title="信頼度"
        )
        return fig
    
    def _create_competitor_chart(self, competitor_data: pd.DataFrame) -> go.Figure:
        """競合比較チャート作成"""
        fig = go.Figure()
        
        if 'brand' in competitor_data.columns and 'market_share' in competitor_data.columns:
            fig = px.pie(
                competitor_data,
                values='market_share',
                names='brand',
                title='市場シェア分布'
            )
        
        return fig