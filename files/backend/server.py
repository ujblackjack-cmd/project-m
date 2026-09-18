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
import librosa
import score_tracking

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

# MusicXML 기준 특징(크로마)을 파일별로 한 번만 계산해서 재사용하기 위한 캐시
reference_cache = score_tracking.ReferenceCache()

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
    """
    실시간 연주 동기화 웹소켓.

    [프로토콜]
    1) 연결 직후, 클라이언트는 먼저 텍스트(JSON) 메시지로 어떤 악보를 기준으로 추적할지 알려준다:
         {"filename": "내악보.musicxml"}
       (업로드 시 저장된 파일명, UPLOAD_DIR 기준 상대경로)
    2) 그 이후부터는 기존과 동일하게 오디오 청크(Float32 PCM 바이너리)를 계속 전송한다.
    3) 서버는 청크마다 JSON으로 상태를 응답한다.

    [동작 모드 — 2가지로 자동 분기됨]
    - MusicXML 업로드인 경우: 크로마 특징 + Online DTW로 실제 음높이를 비교해서
      정확한 마디 단위 위치를 추적한다 (아래 '정밀 추적 모드').
    - PDF/이미지 업로드인 경우: 아직 그 악보의 '정답 음' 정보가 없다(OMR 미연동 상태이므로).
      이 경우 기존과 동일하게 RMS(음량) 기반 단순 감지로 폴백한다. 즉 "얼마나 정확히
      추적되는가"는 OMR이 실제로 붙어야 근본적으로 개선된다 — 이건 오디오 분석만으로는
      해결할 수 없는 부분이라는 점을 명확히 해둔다.
    """
    await websocket.accept()
    print("🎤 클라이언트와 오디오 스트림 웹소켓 연결 성공")

    tracker = None
    measures_info = None
    hop_sec = None
    last_measure = None
    rolling_buffer = np.zeros(0, dtype=np.float32)
    total_samples_received = 0
    frames_processed = 0
    # [설계 포인트] 매번 버퍼 길이가 달라지는 상태에서 크로마를 통째로 다시 계산하면,
    # CQT 특성상 "같은 순간"인데도 계산할 때마다 경계(edge) 부분 값이 조금씩 달라져서
    # 추적이 마디 사이를 왔다갔다 흔들리는 문제가 생긴다(예전 프로토타입에서 겪었던 것과 동일한 종류).
    # -> 버퍼를 '고정 길이' 윈도우로만 유지하고, 매 청크마다 "새로 들어온 만큼"의
    #    프레임만 순서대로 하나씩 트래커에 넣어서, 실제 연속 스트리밍과 최대한
    #    비슷한 방식으로(경계 흔들림 최소화) 처리한다.
    ANALYSIS_WINDOW_SAMPLES = score_tracking.SR * 1  # 크로마 계산에 쓰는 고정 분석 윈도우(1초)
    MIN_SAMPLES_FOR_CHROMA = ANALYSIS_WINDOW_SAMPLES  # 이 길이가 찰 때까지는 계산 보류

    mode = "rms"  # 기본은 기존 방식(RMS). 초기화 메시지로 MusicXML이 확인되면 "dtw"로 전환

    try:
        # --- 1) 초기화 메시지 수신: 어떤 악보를 기준으로 추적할지 결정 ---
        init_raw = await websocket.receive_text()
        try:
            init_msg = json.loads(init_raw)
            filename = init_msg.get("filename", "")
        except (json.JSONDecodeError, AttributeError):
            filename = ""

        xml_path = os.path.join(UPLOAD_DIR, filename) if filename else ""
        if filename and os.path.splitext(filename)[1].lower() in (".musicxml", ".xml") and os.path.exists(xml_path):
            try:
                ref = reference_cache.get(xml_path)
                tracker = score_tracking.OnlineDTW(ref["chroma"], window_sec=1.2, hop_sec=ref["hop_sec"])
                measures_info = ref["measures_info"]
                hop_sec = ref["hop_sec"]
                mode = "dtw"
                print(f"[audio-sync] '{filename}' 기준 정밀 추적 모드(DTW) 활성화")
            except Exception as e:
                print(f"[audio-sync] 기준 특징 생성 실패, RMS 모드로 폴백: {e}")
                mode = "rms"
        else:
            print(f"[audio-sync] MusicXML 기준을 찾지 못해 RMS(단순 음량) 모드로 동작합니다 "
                  f"(filename='{filename}'). PDF/이미지 악보는 OMR이 연동되기 전까지 정밀 추적이 불가능합니다.")

        # --- 2) 오디오 청크 스트리밍 루프 ---
        while True:
            data = await websocket.receive_bytes()
            audio_array = np.frombuffer(data, dtype=np.float32)
            if len(audio_array) == 0:
                continue

            if mode == "dtw":
                rolling_buffer = np.concatenate([rolling_buffer, audio_array])
                total_samples_received += len(audio_array)
                if len(rolling_buffer) > ANALYSIS_WINDOW_SAMPLES:
                    rolling_buffer = rolling_buffer[-ANALYSIS_WINDOW_SAMPLES:]

                if len(rolling_buffer) < MIN_SAMPLES_FOR_CHROMA:
                    continue  # 아직 고정 분석 윈도우가 다 안 찼음

                chroma = librosa.feature.chroma_cqt(
                    y=rolling_buffer, sr=score_tracking.SR, hop_length=score_tracking.HOP
                )
                n_total_frames = chroma.shape[1]
                # 이번 청크로 인해 "새로 확정된" 프레임 개수만큼만 순서대로 트래커에 투입
                # (전체를 다 넣으면 예전에 이미 처리한 프레임을 중복 처리하게 됨)
                expected_new_frames = max(1, len(audio_array) // score_tracking.HOP)
                new_frame_start = max(0, n_total_frames - expected_new_frames)
                # 아직 한 번도 처리 안 했다면(윈도우가 막 찼을 때) 마지막 프레임 하나만 시작점으로
                if frames_processed == 0:
                    new_frame_start = n_total_frames - 1

                measure = last_measure
                is_trigger = False
                confidence = 0.0
                for f in range(new_frame_start, n_total_frames):
                    live_vec = chroma[:, f]
                    j_est = tracker.step(live_vec)
                    ref_t = j_est * hop_sec
                    measure = score_tracking.ref_time_to_measure(ref_t, measures_info)
                    confidence = max(0.0, 1.0 - tracker.last_cost)
                    if measure != last_measure:
                        is_trigger = True
                        last_measure = measure
                    frames_processed += 1

                await websocket.send_text(json.dumps({
                    "status": "trigger" if is_trigger else "tracking",
                    "mode": "dtw",
                    "measure": measure,
                    "ref_time": round(j_est * hop_sec, 3),
                    "confidence": round(confidence, 3),
                }))

            else:  # mode == "rms" (기존 로직 그대로 유지 — 하위호환)
                rms = np.sqrt(np.mean(audio_array ** 2))
                if rms > 0.08:
                    await websocket.send_text(json.dumps({
                        "status": "trigger",
                        "mode": "rms",
                        "message": "Note detected!",
                        "rms": float(rms),
                    }))

    except WebSocketDisconnect:
        print("🔌 오디오 스트림 웹소켓 연결 종료")

if __name__ == "__main__":
    import uvicorn
    # 서버 실행 (포트 8000)
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)