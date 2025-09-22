"""
論文要約・分析モジュール
Google Gemini APIを使用して論文の要約とトレンド分析を実行
"""

import json
import time
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import google.generativeai as genai


class PaperSummarizer:
    """論文要約クラス"""
    
    def __init__(self, api_key: str):
        """
        初期化
        
        Args:
            api_key: Gemini API キー
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def summarize_paper(self, paper: Dict) -> Dict:
        """
        単一の論文を要約
        
        Args:
            paper: 論文データ
        
        Returns:
            要約結果を含む辞書
        """
        # プロンプトの構築
        prompt = f"""
以下の論文を日本語で要約してください。

【タイトル】
{paper.get('title', 'N/A')}

【要旨】
{paper.get('abstract', 'No abstract available')}

【要約フォーマット】
1. 主要な発見（3つの箇条書き）
2. 使用された成分・技術
3. 潜在的な美容・健康への応用
4. 重要度スコア（1-10）

回答は必ずJSON形式で返してください：
{{
    "key_findings": ["発見1", "発見2", "発見3"],
    "ingredients_tech": ["成分1", "成分2"],
    "applications": ["応用1", "応用2"],
    "importance_score": 8,
    "summary_jp": "50文字以内の要約"
}}
"""
        
        try:
            # Gemini APIを呼び出し
            response = self.model.generate_content(prompt)
            
            # レスポンスからテキスト抽出
            text = response.text
            
            # JSONブロックを抽出（```json...```形式に対応）
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            # JSONパース
            try:
                summary_data = json.loads(text.strip())
            except json.JSONDecodeError:
                # パース失敗時のフォールバック
                summary_data = {
                    "key_findings": ["要約生成に失敗しました"],
                    "ingredients_tech": [],
                    "applications": [],
                    "importance_score": 5,
                    "summary_jp": paper.get('title', 'N/A')[:50]
                }
            
            # 元の論文データと統合
            paper['ai_summary'] = summary_data
            paper['summarized_at'] = datetime.now().isoformat()
            
            # レート制限対策（無料枠: 15 RPM）
            time.sleep(4)  # 60秒/15リクエスト = 4秒/リクエスト
            
            return paper
            
        except Exception as e:
            print(f"要約エラー: {e}")
            paper['ai_summary'] = {
                "error": str(e),
                "key_findings": [],
                "ingredients_tech": [],
                "applications": [],
                "importance_score": 0,
                "summary_jp": "要約失敗"
            }
            return paper
    
    def batch_summarize(self, papers: List[Dict], 
                       max_papers: int = 10) -> List[Dict]:
        """
        複数の論文をバッチ要約
        
        Args:
            papers: 論文リスト
            max_papers: 最大処理数（無料枠のため制限）
        
        Returns:
            要約済み論文リスト
        """
        summarized_papers = []
        papers_to_process = papers[:max_papers]
        total = len(papers_to_process)
        
        for idx, paper in enumerate(papers_to_process, 1):
            print(f"要約中 [{idx}/{total}]: {paper['title'][:50]}...")
            summarized = self.summarize_paper(paper)
            summarized_papers.append(summarized)
        
        return summarized_papers
    
    def analyze_trends(self, all_papers: Dict[str, List[Dict]]) -> Dict:
        """
        全論文からトレンドを分析
        
        Args:
            all_papers: キーワードごとの論文辞書
        
        Returns:
            トレンド分析結果
        """
        # 成分・技術の出現頻度をカウント
        ingredient_counts = {}
        application_counts = {}
        keyword_scores = {}
        total_papers = 0
        
        for keyword, papers in all_papers.items():
            keyword_scores[keyword] = {
                'paper_count': len(papers),
                'avg_importance': 0,
                'top_ingredients': [],
                'top_applications': []
            }
            
            importance_sum = 0
            
            for paper in papers:
                if 'ai_summary' in paper:
                    summary = paper['ai_summary']
                    
                    # 成分・技術をカウント
                    for ingredient in summary.get('ingredients_tech', []):
                        if ingredient:
                            ingredient_counts[ingredient] = ingredient_counts.get(ingredient, 0) + 1
                    
                    # 応用分野をカウント
                    for application in summary.get('applications', []):
                        if application:
                            application_counts[application] = application_counts.get(application, 0) + 1
                    
                    # 重要度スコアを集計
                    importance_sum += summary.get('importance_score', 0)
                    total_papers += 1
            
            # キーワードごとの平均重要度
            if len(papers) > 0:
                keyword_scores[keyword]['avg_importance'] = importance_sum / len(papers)
        
        # トップ成分・応用を抽出
        top_ingredients = sorted(
            ingredient_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:20]
        
        top_applications = sorted(
            application_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # トレンド分析結果
        trend_analysis = {
            'analysis_date': datetime.now().isoformat(),
            'total_papers_analyzed': total_papers,
            'keyword_analysis': keyword_scores,
            'top_ingredients': [
                {'name': name, 'count': count} 
                for name, count in top_ingredients
            ],
            'top_applications': [
                {'name': name, 'count': count} 
                for name, count in top_applications
            ],
            'trend_insights': self._generate_insights(
                keyword_scores, top_ingredients, top_applications
            )
        }
        
        return trend_analysis
    
    def _generate_insights(self, keyword_scores: Dict, 
                          top_ingredients: List, 
                          top_applications: List) -> List[str]:
        """
        トレンドからインサイトを生成
        
        Args:
            keyword_scores: キーワードスコア
            top_ingredients: トップ成分
            top_applications: トップ応用
        
        Returns:
            インサイトのリスト
        """
        insights = []
        
        # 最も注目度の高いキーワード
        if keyword_scores:
            top_keyword = max(
                keyword_scores.items(), 
                key=lambda x: x[1]['avg_importance']
            )
            insights.append(
                f"最も注目度が高いキーワード: {top_keyword[0]} "
                f"(平均重要度: {top_keyword[1]['avg_importance']:.1f})"
            )
        
        # 最も研究が活発な成分
        if top_ingredients and len(top_ingredients) > 0:
            insights.append(
                f"最も研究が活発な成分: {top_ingredients[0][0]} "
                f"({top_ingredients[0][1]}件の論文で言及)"
            )
        
        # 主要な応用分野
        if top_applications and len(top_applications) > 0:
            app_names = [app[0] for app in top_applications[:3]]
            insights.append(
                f"主要な応用分野: {', '.join(app_names)}"
            )
        
        # 論文数によるトレンド判定
        high_volume_keywords = [
            k for k, v in keyword_scores.items() 
            if v['paper_count'] >= 5
        ]
        if high_volume_keywords:
            insights.append(
                f"研究が活発な分野: {', '.join(high_volume_keywords[:3])}"
            )
        
        return insights
    
    def save_analysis(self, analysis: Dict, output_path: Path):
        """
        分析結果を保存
        
        Args:
            analysis: 分析結果
            output_path: 出力パス
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        print(f"分析結果を保存: {output_path}")


# テスト用コード
if __name__ == "__main__":
    # サンプルデータ
    sample_paper = {
        'title': 'Effects of NMN supplementation on skin aging',
        'abstract': 'This study investigates the effects of NMN on skin health...',
        'pmid': '12345678'
    }
    
    # API キーは環境変数から取得することを推奨
    # summarizer = PaperSummarizer(api_key="YOUR_API_KEY")
    # result = summarizer.summarize_paper(sample_paper)
    # print(json.dumps(result, ensure_ascii=False, indent=2))
