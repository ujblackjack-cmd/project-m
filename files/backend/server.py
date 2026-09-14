"""
server.py
- 프론트엔드(React)로부터 악보 파일(MusicXML, PDF, 이미지)을 업로드 받아
  전처리 및 시퀀스 추출을 수행하는 FastAPI 백엔드 서버입니다.
"""
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from ingest_score import process_uploaded_file
from fastapi import WebSocket, WebSocketDisconnect
import numpy as np
import json

app = FastAPI(title="AI Music Lesson Assistant API", version="1.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.mount("/etc", StaticFiles(directory=BASE_DIR), name="etc")

# 프론트엔드(React)와의 원활한 통신을 위한 CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 서비스 시 프론트엔드 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 업로드된 파일을 임시로 저장할 폴더
UPLOAD_DIR = "etc"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.get("/")
def health_check():
    return {"status": "running", "message": "AI Music Lesson Assistant Backend is active!"}

@app.post("/api/score/upload")
async def upload_score(file: UploadFile = File(...)):
    """
    악보 파일을 업로드받아 파싱 후 DTW용 시퀀스를 반환하는 엔드포인트
    """
    try:
        # 안전한 파일 저장 경로 설정
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # 파일 서버 로컬에 임시 저장
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
            
        print(f"\n[API 요청 수신] 파일 업로드됨: {file.filename}")
        
        # ingest_score 파이프라인 태우기
        sequence = process_uploaded_file(file_path)
        
        fixed_sequence = sequence
        if isinstance(sequence, list) and len(sequence) > 0 and isinstance(sequence[0], str):
            fixed_sequence = [
                path if path.startswith("etc/") else f"etc/{path}" 
                for path in sequence
            ]
        
        return {
            "success": True,
            "filename": file.filename,
            "sequence_count": len(sequence) if isinstance(sequence, list) else "PDF/Image pages",
            "sequence_data": fixed_sequence
        }

    except Exception as e:
        print(f"[에러 발생] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/audio-sync")
async def audio_sync_websocket(websocket: WebSocket):
    await websocket.accept()
    print("🎤 클라이언트와 오디오 스트림 웹소켓 연결 성공")
    try:
        while True:
            # 프론트엔드에서 전송한 오디오 바이너리 데이터 수신
            data = await websocket.receive_bytes()
            
            # 바이트 데이터를 numpy 배열(Float32)로 변환
            audio_array = np.frombuffer(data, dtype=np.float32)
            
            if len(audio_array) > 0:
                # 오디오 에너지(RMS, 볼륨) 계산
                rms = np.sqrt(np.mean(audio_array**2))
                
                # 임계값(Threshold)을 넘는 연주 소리가 감지되면 트리거 전송
                # (추후 이 부분을 librosa 등을 활용한 피치(음높이) 분석으로 고도화할 수 있습니다)
                if rms > 0.08:
                    await websocket.send_text(json.dumps({
                        "status": "trigger", 
                        "message": "Note detected!",
                        "rms": float(rms)
                    }))
            
    except WebSocketDisconnect:
        print("🔌 오디오 스트림 웹소켓 연결 종료")

if __name__ == "__main__":
    import uvicorn
    # 서버 실행 (포트 8000)
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)