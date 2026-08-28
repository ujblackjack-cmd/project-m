# 피아노 Score Following 프로토타입

## 무엇을 검증했나
"악보(정답)를 그대로 연주한 오디오"와 "사람이 템포를 오락가락하며 연주했다고 가정한 오디오"를
크로마(chroma) 특징 + DTW(Dynamic Time Warping)로 정렬해서,
**연주 중인 시각으로부터 현재 악보상 몇 마디를 연주하고 있는지 실시간으로 추정**할 수 있는지 확인했습니다.

결과: 2.5~5초 구간에서 느리게 치고, 5~7.5초 구간에서 빠르게 쳐도(`02_simulate_performance.py`에서
인위적으로 템포를 0.7배/1.35배로 왜곡) 정렬이 정확히 그 구간만큼 휘어지며 따라잡는 것을 확인했습니다
(`dtw_alignment_result.png` 상단 그래프 참고).

## 파일 구성
| 파일 | 역할 |
|---|---|
| `01_make_score.py` | 테스트용 피아노 악보(MusicXML+MIDI) 생성, 마디-시각 매핑 저장 |
| `02_simulate_performance.py` | 실제 마이크 녹음 대신 템포를 왜곡시켜 '연주'를 시뮬레이션 |
| `03_align_and_track.py` | 크로마 추출 + DTW 정렬 + 마디 추적 + 시각화 (핵심 로직) |
| `piano_test_score.musicxml` | 생성된 악보 |
| `reference_audio.wav` | 정답 연주 오디오 |
| `performance_audio.wav` | 시뮬레이션된 '사용자' 연주 오디오 |
| `dtw_alignment_result.png` | 정렬 결과 시각화 |

## 이 프로토타입의 한계 (의도적으로 단순화한 부분)
1. **배치(오프라인) DTW**를 썼습니다. 실제 서비스는 연주가 끝나야 정렬되면 안 되고,
   매 프레임(~20ms)마다 실시간으로 "지금 위치"를 갱신해야 합니다 → **Online DTW**로 교체 필요.
2. 실제 마이크 대신 합성 오디오로 테스트했습니다. 실제 피아노 소리(특히 잔향, 페달, 배음, 주변 소음)는
   크로마 특징의 잡음을 늘리므로 견고성(robustness) 튜닝이 더 필요합니다.
3. 4마디짜리 짧은 곡으로 검증했습니다. 실제 곡은 훨씬 길고 반복 구간(레페티션, 다카포 등)이 있어서
   "비슷한 화성 패턴이 여러 번 나올 때 헷갈리지 않게" 하는 처리가 추가로 필요합니다.

## 다음 단계 로드맵
1. **Online DTW 구현** — Dixon(2005)의 OLTW 알고리즘 기반, 매 프레임 O(1)~O(w) (w=탐색 윈도우)로
   현재 위치를 갱신. `librosa.sequence.dtw`는 배치용이라 여기엔 못 씀 — 직접 구현 필요.
2. **실시간 마이크 스트리밍 연동** — `sounddevice`로 콜백 기반 오디오 캡처, 버퍼 단위로 크로마 계산.
3. **자동 페이지 넘김 트리거** — 추정 위치가 다음 페이지 첫 마디를 지나면 이벤트 발생.
4. **적응형 메트로놈** — 악보에서 뽑은 BPM을 기준으로 클릭 사운드 스케줄링. 추적된 실제 템포에 맞춰
   메트로놈이 사용자를 따라가게 할지, 아니면 기준 템포를 고정으로 유지해서 "정확한 박자 훈련용"으로
   쓸지는 제품 설계 선택.
5. **레슨 피드백 LLM 모듈** — 이건 이 스크립트와 별도 트랙으로 지금 바로 시작 가능. (다음 메시지에서
   원하시면 프로토타입 만들어드릴게요: 레슨 노트 텍스트 + 악보 다이나믹 마킹 + 정렬 결과에서 뽑은
   박자 편차/음량 편차를 LLaMA에 넣어 피드백 생성)

## 재현 방법
```bash
pip install music21 librosa pretty_midi soundfile matplotlib
apt-get install fluidsynth fluid-soundfont-gm
python3 01_make_score.py
python3 02_simulate_performance.py
fluidsynth -ni /usr/share/sounds/sf2/FluidR3_GM.sf2 piano_test_score.mid -F reference_audio.wav -r 22050
fluidsynth -ni /usr/share/sounds/sf2/FluidR3_GM.sf2 performance_simulated.mid -F performance_audio.wav -r 22050
python3 03_align_and_track.py
```
