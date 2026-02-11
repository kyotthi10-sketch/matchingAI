import os
import json
import asyncio
from typing import Dict, List, Tuple, Optional
from collections import Counter, defaultdict
import google.generativeai as genai

# Gemini API設定
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# 5段階スコア
STAR_MAP = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}


class AIMatchingEngine:
    """Google Gemini APIを使った高度なマッチングエンジン"""
    
    def __init__(self):
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            # Gemini 2.0 Flash を使用（最新で高速）
            self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        else:
            self.model = None
    
    async def analyze_profile(
        self,
        category: str,
        answers: List[Tuple[int, str]],
        question_data: Dict
    ) -> Dict:
        """
        ユーザーの回答をAIで分析してプロフィールを生成
        
        Args:
            category: カテゴリー (friendship/dating/gaming/business)
            answers: [(question_id, answer), ...]
            question_data: {question_id: question_text, ...}
        
        Returns:
            分析結果 {personality_traits, communication_style, preferences, ...}
        """
        if not self.model:
            return self._basic_profile_analysis(answers, question_data)
        
        # 回答を整形
        answer_text = self._format_answers_for_ai(answers, question_data)
        
        prompt = f"""あなたは{category}マッチングの専門家です。以下のユーザーの回答を分析し、詳細なプロフィールを作成してください。

【カテゴリー】{category}

【ユーザーの回答】
{answer_text}

以下のJSON形式で分析結果を返してください：
{{
  "personality_summary": "性格の要約（3-4文）",
  "key_traits": ["特徴1", "特徴2", "特徴3", "特徴4", "特徴5"],
  "communication_style": "コミュニケーションスタイルの説明",
  "preferences": {{
    "ideal_match": "理想的な相手の特徴",
    "priorities": ["優先事項1", "優先事項2", "優先事項3"]
  }},
  "compatibility_factors": ["相性判定に重要な要素1", "要素2", "要素3"],
  "match_keywords": ["マッチング用キーワード1", "キーワード2", "キーワード3", "キーワード4", "キーワード5"]
}}

JSONのみを返し、他の説明は不要です。"""

        try:
            # 非同期でGemini APIを呼び出し
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1500,
                }
            )
            
            result_text = response.text.strip()
            
            # JSONの抽出（```json ``` で囲まれている場合に対応）
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            return json.loads(result_text)
            
        except Exception as e:
            print(f"Gemini API analysis error: {e}")
            return self._basic_profile_analysis(answers, question_data)
    
    def _format_answers_for_ai(
        self,
        answers: List[Tuple[int, str]],
        question_data: Dict
    ) -> str:
        """回答をAI分析用に整形"""
        lines = []
        for qid, ans in answers:
            q_text = question_data.get(qid, f"質問{qid}")
            stars = STAR_MAP.get(ans, 3)
            lines.append(f"Q: {q_text}\nA: {ans} (★{'★'*stars}{'☆'*(5-stars)})")
        return "\n\n".join(lines)
    
    def _basic_profile_analysis(
        self,
        answers: List[Tuple[int, str]],
        question_data: Dict
    ) -> Dict:
        """基本的なプロフィール分析（AI不使用時のフォールバック）"""
        # 回答の傾向を分析
        answer_counts = Counter([ans for _, ans in answers])
        avg_score = sum(STAR_MAP.get(ans, 3) for _, ans in answers) / max(len(answers), 1)
        
        return {
            "personality_summary": f"平均スコア: {avg_score:.1f}",
            "key_traits": list(answer_counts.keys())[:5],
            "communication_style": "標準",
            "preferences": {
                "ideal_match": "類似した価値観を持つ相手",
                "priorities": ["価値観の一致", "コミュニケーション", "共通の興味"]
            },
            "compatibility_factors": ["回答の類似性", "スコアの近さ"],
            "match_keywords": []
        }
    
    async def calculate_compatibility(
        self,
        category: str,
        user1_profile: Dict,
        user2_profile: Dict,
        user1_answers: List[Tuple[int, str]],
        user2_answers: List[Tuple[int, str]]
    ) -> Dict:
        """
        2人のユーザーの相性を詳細分析
        
        Returns:
            {
                "overall_score": 0.0-1.0,
                "category_scores": {...},
                "strengths": [...],
                "potential_challenges": [...],
                "conversation_starters": [...]
            }
        """
        if not self.model:
            return self._basic_compatibility(user1_answers, user2_answers)
        
        # 基本スコアを計算
        basic_score = self._calculate_answer_similarity(user1_answers, user2_answers)
        
        prompt = f"""あなたは{category}マッチングの専門家です。2人のユーザーの相性を分析してください。

【ユーザー1のプロフィール】
{json.dumps(user1_profile, ensure_ascii=False, indent=2)}

【ユーザー2のプロフィール】
{json.dumps(user2_profile, ensure_ascii=False, indent=2)}

【基本相性スコア】{basic_score:.0%}（回答の一致率）

以下のJSON形式で相性分析結果を返してください：
{{
  "overall_score": 0.85,
  "analysis_summary": "相性の総合評価（2-3文）",
  "strengths": ["強み1", "強み2", "強み3"],
  "potential_challenges": ["注意点1", "注意点2"],
  "conversation_starters": [
    "会話のきっかけ1（具体的な話題）",
    "会話のきっかけ2",
    "会話のきっかけ3"
  ],
  "recommendation": "マッチングの推奨度（high/medium/low）とその理由"
}}

overall_scoreは0.0〜1.0の範囲で、基本相性スコアも参考にしてください。
JSONのみを返し、他の説明は不要です。"""

        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config={
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1200,
                }
            )
            
            result_text = response.text.strip()
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            result = json.loads(result_text)
            result["basic_score"] = basic_score
            return result
            
        except Exception as e:
            print(f"Gemini compatibility analysis error: {e}")
            return self._basic_compatibility(user1_answers, user2_answers)
    
    def _calculate_answer_similarity(
        self,
        answers1: List[Tuple[int, str]],
        answers2: List[Tuple[int, str]]
    ) -> float:
        """回答の類似度を計算（0.0〜1.0）"""
        dict1 = {qid: ans for qid, ans in answers1}
        dict2 = {qid: ans for qid, ans in answers2}
        
        common_qids = set(dict1.keys()) & set(dict2.keys())
        if not common_qids:
            return 0.0
        
        # 完全一致のカウント
        exact_matches = sum(1 for qid in common_qids if dict1[qid] == dict2[qid])
        
        # スコア差も考慮
        score_diff_sum = 0
        for qid in common_qids:
            score1 = STAR_MAP.get(dict1[qid], 3)
            score2 = STAR_MAP.get(dict2[qid], 3)
            score_diff_sum += abs(score1 - score2)
        
        # 完全一致率 (0-1) と スコア類似度 (0-1) の平均
        exact_ratio = exact_matches / len(common_qids)
        score_similarity = 1.0 - (score_diff_sum / (len(common_qids) * 4))  # 最大差は4
        
        return (exact_ratio * 0.6 + score_similarity * 0.4)
    
    def _basic_compatibility(
        self,
        answers1: List[Tuple[int, str]],
        answers2: List[Tuple[int, str]]
    ) -> Dict:
        """基本的な相性分析（AI不使用時）"""
        score = self._calculate_answer_similarity(answers1, answers2)
        
        return {
            "overall_score": score,
            "basic_score": score,
            "analysis_summary": f"回答の一致率に基づく相性: {score:.0%}",
            "strengths": ["回答パターンの類似性"] if score > 0.6 else [],
            "potential_challenges": ["価値観の違い"] if score < 0.4 else [],
            "conversation_starters": ["共通の興味について話してみましょう"],
            "recommendation": "high" if score > 0.7 else ("medium" if score > 0.5 else "low")
        }
    
    async def generate_icebreaker(
        self,
        category: str,
        user1_name: str,
        user2_name: str,
        compatibility: Dict
    ) -> str:
        """マッチング成立時のアイスブレイクメッセージを生成"""
        if not self.model:
            return f"🎉 {user1_name}さんと{user2_name}さんがマッチしました！お互いに挨拶してみましょう！"
        
        prompt = f"""あなたは{category}マッチングサービスのAIアシスタントです。
        
{user1_name}さんと{user2_name}さんがマッチしました。

【相性分析】
{json.dumps(compatibility, ensure_ascii=False, indent=2)}

2人が自然に会話を始められるよう、以下の要素を含む温かいアイスブレイクメッセージを作成してください：
1. マッチングのお祝い
2. 相性の良さの簡単な説明
3. 具体的な会話のきっかけ（1-2個）
4. 前向きな締めくくり

200文字程度で、フレンドリーな口調で書いてください。
絵文字も適度に使ってOKです。"""

        try:
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config={
                    "temperature": 0.8,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 400,
                }
            )
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Gemini icebreaker generation error: {e}")
            score = compatibility.get("overall_score", 0.5)
            return f"🎉 {user1_name}さんと{user2_name}さんがマッチしました！相性度: {score:.0%}\n\n{compatibility.get('conversation_starters', ['お互いの趣味について話してみましょう！'])[0]}"


# =========================================================
# カテゴリー別プロフィール集計
# =========================================================
def build_category_profile(
    answers: List[Tuple[int, str]],
    questions: List[Dict]
) -> Tuple[Dict[str, str], Dict[str, int]]:
    """
    カテゴリー別に回答を集計
    
    Returns:
        picks: {subcategory: most_common_answer}
        meters: {subcategory: average_stars}
    """
    qid_to_subcat = {q["id"]: q.get("category") for q in questions}
    
    by_subcat = defaultdict(list)
    for qid, ans in answers:
        subcat = qid_to_subcat.get(qid)
        if subcat and ans in STAR_MAP:
            by_subcat[subcat].append(ans)
    
    picks = {}
    meters = {}
    for subcat, ans_list in by_subcat.items():
        c = Counter(ans_list)
        picks[subcat] = c.most_common(1)[0][0]
        meters[subcat] = int(round(sum(STAR_MAP[x] for x in ans_list) / len(ans_list)))
    
    return picks, meters


def category_compatibility_score(
    picks1: Dict[str, str],
    picks2: Dict[str, str]
) -> float:
    """カテゴリー別の一致率を計算"""
    common_cats = set(picks1.keys()) & set(picks2.keys())
    if not common_cats:
        return 0.0
    
    matches = sum(1 for cat in common_cats if picks1[cat] == picks2[cat])
    return matches / len(common_cats)


# =========================================================
# 使用例（テスト用）
# =========================================================
async def test_matching_engine():
    """マッチングエンジンのテスト"""
    engine = AIMatchingEngine()
    
    # サンプルデータ
    sample_answers_1 = [(101, "D"), (102, "E"), (103, "C"), (104, "B"), (105, "D")]
    sample_answers_2 = [(101, "D"), (102, "D"), (103, "C"), (104, "C"), (105, "E")]
    
    question_data = {
        101: "初対面の人とも比較的すぐに打ち解けられる。",
        102: "雑談や会話を楽しむことが好きだ。",
        103: "深い話や真面目な議論も好きだ。",
        104: "テキストよりも通話やVCの方が好きだ。",
        105: "頻繁に連絡を取り合う関係が好きだ。",
    }
    
    # プロフィール分析
    print("=== プロフィール分析 (Gemini) ===")
    profile1 = await engine.analyze_profile("friendship", sample_answers_1, question_data)
    print(json.dumps(profile1, ensure_ascii=False, indent=2))
    
    profile2 = await engine.analyze_profile("friendship", sample_answers_2, question_data)
    print(json.dumps(profile2, ensure_ascii=False, indent=2))
    
    # 相性分析
    print("\n=== 相性分析 (Gemini) ===")
    compatibility = await engine.calculate_compatibility(
        "friendship",
        profile1,
        profile2,
        sample_answers_1,
        sample_answers_2
    )
    print(json.dumps(compatibility, ensure_ascii=False, indent=2))
    
    # アイスブレイク
    print("\n=== アイスブレイク (Gemini) ===")
    icebreaker = await engine.generate_icebreaker(
        "friendship",
        "ユーザー1",
        "ユーザー2",
        compatibility
    )
    print(icebreaker)


if __name__ == "__main__":
    asyncio.run(test_matching_engine())
