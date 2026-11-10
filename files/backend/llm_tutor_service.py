import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai

from pydantic import BaseModel
from typing import Optional

router = APIRouter()

FEEDBACK_FILE = "feedbacks.json"
REF_FILE = "references.json"

import json
def load_json_file(filepath):
    if not os.path.exists(filepath):
        return {}
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return {}

class TutorRequest(BaseModel):
    filename: str
    current_measure: Optional[int] = 1
    difficulty: Optional[str] = "초급" # 기본값 초급 설정

@router.post("/coaching")
async def get_llm_coaching(req: TutorRequest):
    feedbacks_data = load_json_file(FEEDBACK_FILE)
    references_data = load_json_file(REF_FILE)

    file_feedbacks = feedbacks_data.get(req.filename, [])
    file_ref = references_data.get(req.filename, {})
    timestamps = file_ref.get("measure_timestamps", {})

    current_m = str(req.current_measure)
    related_memos = [
        fb.get("text", "") for fb in file_feedbacks 
        if str(fb.get("measure")) == current_m
    ]
    
    sec = timestamps.get(current_m, None)
    time_info = f"{sec}초" if sec is not None else "타임스탬프 미지정"

    # 난이도별 맞춤 가이드라인 설정
    difficulty_guide = {
        "초급": "기초적인 박자 안정성, 손가락 번호, 올바른 손 모양, 틀리지 않고 치는 것에 초점을 맞춰 아주 쉽고 격려하는 톤으로 2~3줄 코칭해주세요.",
        "중급": "템포의 균일함, 양손 밸런스, 기본적인 크레센도/디크레센도 등 표현력에 초점을 맞춰 구체적으로 코칭해주세요.",
        "고급": "미세한 아티큘레이션, 루바토, 페달링 테크닉, 곡의 해석과 음악적 완성도를 높이기 위한 전문적인 조언을 제공해주세요."
    }
    
    selected_guide = difficulty_guide.get(req.difficulty, difficulty_guide["초급"])

    prompt = f"""
당신은 친절하고 전문적인 AI 피아노/음악 레슨 교사입니다.
현재 연주자의 난이도는 [{req.difficulty}]입니다. {selected_guide}

[악보 및 진행 상황]
- 악보 파일명: {req.filename}
- 현재 연주/연습 마디: {req.current_measure}마디
- 교보재 시범 연주 타임스탬프: {time_info}

[선생님의 사전 레슨 메모]
{chr(10).join(f"- {m}" for m in related_memos) if related_memos else "- 해당 마디에 등록된 특이 메모 없음"}

[요청 사항]
1. 현재 {req.current_measure}마디를 연주할 때 난이도 맞춤형 주의사항을 조언해주세요.
2. 참고 영상 타임스탬프({time_info})가 있다면 어떤 부분에 집중해야 하는지 일러주세요.
3. 톤은 난이도에 알맞게 따뜻하고 전문적인 격려의 말투를 사용해주세요.
"""

    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        return {
            "status": "success",
            "measure": req.current_measure,
            "coaching": f"[{req.difficulty} 코칭 - {req.current_measure}마디] 박자와 기본기에 집중하여 연주해보세요!"
        }

    try:
        genai.configure(api_key=gemini_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        return {
            "status": "success",
            "measure": req.current_measure,
            "coaching": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API 호출 실패: {str(e)}")