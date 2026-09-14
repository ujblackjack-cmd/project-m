"""
5단계: 실시간 스트리밍 시뮬레이션 검증

실제 마이크가 없으므로, 이미 만들어둔 performance_audio.wav(템포가 왜곡된 '사용자 연주')를
마치 마이크에서 실시간으로 들어오는 것처럼 프레임 단위(약 23ms)로 하나씩 흘려보낸다.

핵심 검증 포인트: OnlineDTW는 '그 순간까지 들어온 프레임'만 사용하므로,
지난번 배치(오프라인) DTW 결과와 얼마나 비슷하게 나오는지 비교하면
"미래를 못 보는 상태에서도 실시간 추적이 실제로 되는가"를 확인할 수 있다.
"""
import numpy as np
import librosa
import json
import time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from online_dtw_module import OnlineDTW

FONT_PATH = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
fm.fontManager.addfont(FONT_PATH)
plt.rcParams['font.family'] = fm.FontProperties(fname=FONT_PATH).get_name()
plt.rcParams['axes.unicode_minus'] = False

SR = 22050
HOP = 512
HOP_SEC = HOP / SR

# ---- 정답(악보) 특징: 미리 전부 계산 (실제 서비스에서도 악보는 사전 렌더링해두므로 OK) ----
ref_y, _ = librosa.load('reference_audio.wav', sr=SR)
ref_chroma = librosa.feature.chroma_cqt(y=ref_y, sr=SR, hop_length=HOP)

# ---- '연주' 오디오: 실시간 스트리밍처럼 프레임 단위로만 접근 ----
perf_y, _ = librosa.load('performance_audio.wav', sr=SR)
# 참고: 진짜 실시간 서비스에서는 오디오 콜백마다 최근 버퍼(예: 1~2초 rolling window)에 대해
# CQT를 갱신 계산해서 매 프레임의 크로마를 뽑는다. 여기서는 '온라인 DTW 알고리즘 자체'의
# 정확성을 검증하는 것이 목적이므로, 크로마 추출은 배치로 한번에 계산하되
# tracker.step()에는 오직 그 순간까지의 프레임만 순서대로 공급해서 인과성(causality)을 지킨다.
perf_chroma_full = librosa.feature.chroma_cqt(y=perf_y, sr=SR, hop_length=HOP)

with open('measures_info.json') as f:
    measures_info = json.load(f)


def ref_frame_to_measure(ref_frame_idx):
    ref_t = ref_frame_idx * HOP_SEC
    current = measures_info[0]['measure']
    for m in measures_info:
        if ref_t >= m['start_sec']:
            current = m['measure']
        else:
            break
    return current


tracker = OnlineDTW(ref_chroma, window_sec=1.2, hop_sec=HOP_SEC)

n_frames = perf_chroma_full.shape[1]
online_track = []  # (연주 경과시간, 추정 악보시간, 추정 마디)
last_measure = None
page_turn_log = []

wall_clock_start = time.time()
for i in range(n_frames):
    # --- 실시간이라면 여기서 마이크 버퍼로부터 계산한 크로마 벡터를 받아옴 ---
    live_vec = perf_chroma_full[:, i]  # i번째 프레임까지만 사용 (미래 프레임 접근 없음 = 인과적)

    j_est = tracker.step(live_vec)  # <-- 이 시점에서 '미래 정보 없이' 현재 위치만 추정

    perf_t = i * HOP_SEC
    ref_t = j_est * HOP_SEC
    measure = ref_frame_to_measure(j_est)
    online_track.append((perf_t, ref_t, measure))

    if measure != last_measure:
        page_turn_log.append((perf_t, measure))
        last_measure = measure

elapsed_wall = time.time() - wall_clock_start
online_track = np.array([(t[0], t[1]) for t in online_track])

print(f"총 {n_frames}프레임 처리, 실제 계산 소요 시간 {elapsed_wall:.2f}초 "
      f"(오디오 길이 {n_frames*HOP_SEC:.2f}초 -> 실시간보다 "
      f"{'빠름' if elapsed_wall < n_frames*HOP_SEC else '느림'}, "
      f"배속 {n_frames*HOP_SEC/elapsed_wall:.1f}x)")

print("\n=== 마디 전환(자동 페이지 넘김 트리거) 감지 시점 ===")
for t, m in page_turn_log:
    print(f"연주 경과 {t:5.2f}s 시점에 {m}마디 진입 감지 -> 이 시점에 '페이지 넘김' 이벤트 발생")

# ---- 배치(오프라인) DTW 결과와 비교해서 온라인 버전이 잘 따라가는지 시각적으로 검증 ----
D, wp = librosa.sequence.dtw(X=perf_chroma_full, Y=ref_chroma, metric='cosine')
wp = wp[::-1]
batch_perf_t = np.array([i * HOP_SEC for i, j in wp])
batch_ref_t = np.array([j * HOP_SEC for i, j in wp])

plt.figure(figsize=(10, 6))
plt.plot(batch_perf_t, batch_ref_t, '-', color='#9CA3AF', linewidth=3, label='배치 DTW (오프라인, 미래 정보 포함 - 참고용 정답)')
plt.plot(online_track[:, 0], online_track[:, 1], '-', color='#DC2626', linewidth=1.8, label='Online DTW (실시간, 인과적 추정)')
plt.xlabel('연주 경과 시간 (초)', fontsize=13)
plt.ylabel('추정된 악보(정답) 시간 (초)', fontsize=13)
plt.title('실시간(Online) DTW vs 오프라인(배치) DTW 추적 비교', fontsize=15, fontweight='bold')
plt.legend(loc='upper left', fontsize=11)
plt.tight_layout()
plt.savefig('online_vs_batch_dtw.png', dpi=200)
print("\n비교 시각화 저장 완료: online_vs_batch_dtw.png")

# 정량적 오차 측정: 같은 perf_t 지점에서 online과 batch의 ref_t 차이
batch_interp = np.interp(online_track[:, 0], batch_perf_t, batch_ref_t)
err = np.abs(online_track[:, 1] - batch_interp)
print(f"\n평균 추적 오차: {err.mean():.3f}초, 최대 오차: {err.max():.3f}초 (배치 결과 대비)")
