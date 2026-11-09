# 🎹 AI 스마트 음악 레슨 조수 (AI Music Lesson Assistant)

> **실시간 마이크 연주 추적, 대화형 악보 필기, 교보재 동기화 및 Google Gemini LLM 기반의 원포인트 맞춤형 음악 레슨 웹 애플리케이션**

---

## 📌 프로젝트 소개

이 프로젝트는 피아노 및 악기 연습 환경에서 연주자가 악보를 보며 효율적으로 연습할 수 있도록 돕는 **AI 기반 스마트 레슨 조수 플랫폼**입니다. 

초기 Python 기반의 DTW(Dynamic Time Warping) 오디오-악보 정렬 프로토타입을 발전시켜, 현재는 **웹소켓(WebSocket) 기반 실시간 마이크 오디오 추적**, **HTML5 Canvas 기반 대화형 악보 필기**, **교보재 시범 연주 동기화**, 그리고 **Google Gemini LLM 기반 실시간 레슨 코칭** 기능을 갖춘 풀스택 웹 서비스로 구축되었습니다.

---

## ✨ 주요 기능

### 1. 📄 대화형 악보 뷰어 & 렌더링
* **PDF / 이미지 악보 변환**: PDF 업로드 시 `PyMuPDF`를 통해 고화질 PNG 이미지로 자동으로 분할 및 변환되어 렌더링됩니다.
* **스마트 줌 & responsive 레이아웃**: 40% ~ 300%까지 자유로운 악보 확대/축소 및 반응형 가로/세로 최적화를 제공합니다.
* **Canvas 대화형 필기 툴**: 악보 위에 직접 펜, 형광펜(투명도 조절), 지우개 툴을 이용해 필기 및 원포인트 레슨 마킹이 가능합니다.

### 2. 🎤 실시간 마이크 연주 추적 (Score Following & Sync)
* **WebSocket 오디오 스트리밍**: 브라우저 마이크 입력 오디오(PCM/RMS)를 백엔드로 실시간 전송합니다.
* **실시간 입력 메터 & 상태 인디케이터**: 연주 음량이 실시간 초록색 RMS 레벨 바로 표시되어 녹음 작동 여부를 직관적으로 파악할 수 있습니다.
* **플로팅 마디 배너 & 토스트 알림**: 현재 연주 중인 마디(`🎯 N마디`)가 악보 중앙 상단에 실시간으로 표시되며, 마디 전환 시 알림 토스트와 함께 해당 악보 위치로 자동 스크롤됩니다.

### 3. 🤖 Google Gemini 기반 AI 레슨 코치
* **실시간 원포인트 코칭**: 연주 중인 마디 위치에 맞추어 **선생님의 사전 레슨 메모(`feedbacks.json`)**와 **교보재 시범 연주 타임스탬프(`references.json`)**를 종합 분석합니다.
* **맞춤형 튜터링**: `Gemini 1.5 Flash` LLM 모델이 연주자에게 현재 마디에서 주의해야 할 테크닉, 손모양, 표현법 및 참고 영상 시청 포인트를 친절하게 일러줍니다.

### 4. 🎵 통합 메트로놈 & 레퍼런스 플레이어
* **Web Audio API 메트로놈**: 40 ~ 240 BPM 범위에서 정밀한 틱 사운드 카운트를 제공합니다.
* **시범 연주 플레이어**: 마디별 타임스탬프와 연동되어 구간 반복 및 시범 연주 확인이 가능합니다.

---

## 🛠 기술 스택

### Frontend
- **Framework**: React (Vite)
- **HTTP/Realtime**: Axios, WebSockets, Web Audio API, HTML5 Canvas API
- **Styling**: CSS-in-JS (Custom Dark Theme UI)

### Backend
- **Framework**: FastAPI, Uvicorn
- **Realtime / Network**: `websockets` (Async WebSocket Server)
- **PDF & Audio Processing**: PyMuPDF (`pymupdf`), Librosa, NumPy
- **AI / LLM**: Google Generative AI SDK (`google-generativeai` - Gemini 1.5 Flash)
- **Environment**: Python-dotenv, Pydantic

---

## 📁 프로젝트 구조

```text
project-m/
├── files/
│   ├── backend/                 # FastAPI 백엔드
│   │   ├── server.py            # 메인 FastAPI 서버 및 웹소켓 엔드포인트 (/ws/audio-sync)
│   │   ├── ingest_score.py      # PDF 악보 이미지 변환 및 전처리 (PyMuPDF)
│   │   ├── llm_tutor_service.py # Gemini LLM 기반 AI 레슨 코치 라우터 (/api/tutor/coaching)
│   │   ├── feedbacks.json       # 악보/마디별 선생님 사전 레슨 메모 데이터
│   │   ├── references.json      # 악보/마디별 시범 연주 영상 타임스탬프 데이터
│   │   ├── .env                 # 환경변수 (GEMINI_API_KEY)
│   │   └── requirements.txt     # 백엔드 의존성 패키지 목록
│   │
│   └── front/                   # React 프론트엔드
│       ├── src/
│       │   ├── App.jsx          # 메인 악보 뷰어 & 실시간 마이크 오디오 처리
│       │   ├── AiTutorPanel.jsx # AI 레슨 코치 패널 컴포넌트
│       │   ├── ReferencePlayer.jsx # 레퍼런스 오디오/비디오 플레이어
│       │   └── main.jsx
│       └── package.json
└── README.md
