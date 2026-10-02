import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional

router = APIRouter(prefix="/api/reference", tags=["reference"])

REF_FILE = "references.json"

class ReferenceData(BaseModel):
    filename: str
    video_url: str
    measure_timestamps: Dict[int, float]  # 예: {1: 0.0, 4: 12.5, 8: 28.0}

def load_references():
    if not os.path.exists(REF_FILE):
        return {}
    with open(REF_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_references(data):
    with open(REF_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 1. 특정 악보의 교보재 영상/타임스탬프 정보 조회
@router.get("/{filename:path}")
def get_reference(filename: str):
    data = load_references()
    return data.get(filename, {"video_url": "", "measure_timestamps": {}})

# 2. 교보재 영상 및 마디 타임스탬프 등록/수정
@router.post("")
def save_reference(item: ReferenceData):
    data = load_references()
    data[item.filename] = {
        "video_url": item.video_url,
        "measure_timestamps": item.measure_timestamps
    }
    save_references(data)
    return {"status": "success", "data": data[item.filename]}