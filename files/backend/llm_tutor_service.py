import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import google.generativeai as genai

router = APIRouter(prefix="/api/tutor", tags=["tutor"])

FEEDBACK_FILE = "feedbacks.json"
REF_FILE = "references.json"

class TutorRequest(BaseModel):
    filename: str
    current_measure: Optional[int] = 1

def load_json_file(file_path):
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

@router.post("/coaching")
async def get_llm_coaching(req: TutorRequest):
    # 1. 레슨 메모 및 교보재 타임라인 로드
    feedbacks_data = load_json_file(FEEDBACK_FILE)
    references_data = load_json_file(REF_FILE)

    file_feedbacks = feedbacks_data.get(req.filename, [])
    file_ref = references_data.get(req.filename, {})

    timestamps = file_ref.get("measure_timestamps", {})

    # 2. 현재 마디 관련 메모 및 타임스탬프 추출
    current_m = str(req.current_measure)
    related_memos = [
        fb.get("text", "") for fb in file_feedbacks 
        if str(fb.get("measure")) == current_m
    ]
    
    sec = timestamps.get(current_m, None)
    time_info = f"{sec}초" if sec is not None else "타임스탬프 미지정"

    # 3. 프롬프트 구성
    prompt = f"""
당신은 친절하고 전문적인 AI 피아노/음악 레슨 교사입니다.
학생이 현재 연습 중인 악보의 특정 마디 정보와 선생님의 사전 레슨 메모를 바탕으로 원포인트 코칭을 제공하세요.

[악보 및 진행 상황]
- 악보 파일명: {req.filename}
- 현재 연주/연습 마디: {req.current_measure}마디
- 교보재 시범 연주 타임스탬프: {time_info}

[선생님의 사전 레슨 메모]
{chr(10).join(f"- {m}" for m in related_memos) if related_memos else "- 해당 마디에 등록된 특이 메모 없음"}

[요청 사항]
1. 현재 {req.current_measure}마디를 연주할 때 주의해야 할 테크닉 및 표현법을 2~3줄로 조언해주세요.
2. 참고 영상 타임스탬프({time_info})가 존재한다면, 영상을 시청할 때 어떤 동작(손모양, 페달, 강약 등)에 집중해야 하는지 일러주세요.
3. 톤은 따뜻하고 격려하는 말투(~하세요, ~해보세요)를 사용해주세요.
"""

    # 4. Gemini API 키 확인
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        # 키가 설정되지 않았을 때 반환하는 기본 응답
        return {
            "status": "success",
            "measure": req.current_measure,
            "coaching": f"[{req.current_measure}마디 가이드] {f'영상 {time_info} 구간을 참고하세요. ' if sec else ''}"
                        f"{f'선생님 메모: {related_memos[0]}' if related_memos else '박자와 음형을 일정하게 유지하며 연주해보세요!'}"
        }

    try:
        genai.configure(api_key=gemini_key)
        # 무료 티어 지원 모델 (gemini-1.5-flash 또는 gemini-2.0-flash)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt)

        return {
            "status": "success",
            "measure": req.current_measure,
            "coaching": response.text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API 호출 실패: {str(e)}")