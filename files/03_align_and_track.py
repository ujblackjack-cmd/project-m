"""
3단계 (핵심): Score Following 엔진 프로토타입
- reference_audio.wav (정답=악보를 그대로 연주한 것)
- performance_audio.wav (사용자가 템포를 오락가락하며 연주했다고 가정한 시뮬레이션)
두 오디오에서 크로마 특징을 뽑고, DTW로 정렬해서
"연주 오디오의 t초 지점 = 정답(=악보)의 몇 초/몇 마디 지점"을 알아낸다.

실제 서비스에서는 이 정렬을 온라인(스트리밍) 방식으로 바꿔야 하지만,
먼저 배치(오프라인) DTW로 원리가 맞는지부터 검증한다.
"""
import librosa
import numpy as np
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
for f in fm.fontManager.ttflist:
    if 'NanumGothic' in f.name:
        plt.rcParams['font.family'] = f.name
        break
plt.rcParams['axes.unicode_minus'] = False

SR = 22050
HOP = 512  # 프레임 하나 = 512/22050 ≈ 23ms

ref_y, _ = librosa.load('reference_audio.wav', sr=SR)
perf_y, _ = librosa.load('performance_audio.wav', sr=SR)

# 크로마(chroma) 특징: 12개 음고 클래스(도레미...)의 에너지 분포.
# 화음이 섞여도 "지금 어떤 음들이 울리는가"를 잘 요약해서 폴리포닉(화성) 음악의 정렬에 강함.
ref_chroma = librosa.feature.chroma_cqt(y=ref_y, sr=SR, hop_length=HOP)
perf_chroma = librosa.feature.chroma_cqt(y=perf_y, sr=SR, hop_length=HOP)

print(f"reference 프레임 수: {ref_chroma.shape[1]}  ({ref_chroma.shape[1]*HOP/SR:.2f}s)")
print(f"performance 프레임 수: {perf_chroma.shape[1]}  ({perf_chroma.shape[1]*HOP/SR:.2f}s)")

# DTW로 두 특징 시퀀스를 정렬 (여기선 배치 방식. subseq=False: 전체 대 전체 정렬)
D, wp = librosa.sequence.dtw(X=perf_chroma, Y=ref_chroma, metric='cosine')
wp = wp[::-1]  # (perf_frame_idx, ref_frame_idx) 순서로, 시간 순 정렬

# 프레임 인덱스 -> 초 단위 변환
wp_sec = np.array([[i * HOP / SR, j * HOP / SR] for i, j in wp])

# 마디 정보 로드 (1단계에서 만든 것)
with open('measures_info.json') as f:
    measures_info = json.load(f)

def ref_time_to_measure(ref_t):
    """정답(=악보) 기준 시각 -> 현재 마디 번호"""
    current = measures_info[0]['measure']
    for m in measures_info:
        if ref_t >= m['start_sec']:
            current = m['measure']
        else:
            break
    return current

# 연주 시간축을 기준으로, 몇 초마다 "지금 몇 마디인지" 조회하는 함수 만들기
perf_times = wp_sec[:, 0]
ref_times = wp_sec[:, 1]

def perf_time_to_ref_time(perf_t):
    """DTW 정렬 경로에서 가장 가까운 지점을 찾아 정답 시각으로 변환 (실제 서비스에선 online DTW가 실시간으로 이 값을 계속 업데이트)"""
    idx = np.searchsorted(perf_times, perf_t)
    idx = min(max(idx, 0), len(perf_times) - 1)
    return ref_times[idx]

print("\n=== 성능 검증: 사용자가 실제로 친 시간(왜곡됨) vs 추적된 악보 위치 ===")
test_points = [0.5, 1.5, 3.0, 4.0, 5.5, 6.5, 9.0, 10.0]
for t in test_points:
    if t > perf_times.max():
        continue
    ref_t = perf_time_to_ref_time(t)
    measure = ref_time_to_measure(ref_t)
    print(f"연주 경과시간 {t:5.1f}s  ->  악보상 시각 {ref_t:5.2f}s  ->  현재 {measure}마디")

# 시각화: warping path (얼마나 템포가 휘었는지 한눈에 보임)
plt.figure(figsize=(9, 6))
plt.subplot(2, 1, 1)
plt.plot(perf_times, ref_times, '.', markersize=2, color='#2563eb')
plt.plot([0, perf_times.max()], [0, perf_times.max()], '--', color='gray', linewidth=1, label='정확히 같은 템포라면(기준선)')
for m in measures_info:
    plt.axhline(m['start_sec'], color='#d1d5db', linewidth=0.7)
    plt.text(perf_times.max()*1.01, m['start_sec'], f"{m['measure']}마디", fontsize=8, va='center')
plt.xlabel('사용자 연주 경과 시간 (초)')
plt.ylabel('정렬된 악보(정답) 시간 (초)')
plt.title('DTW 정렬 경로: 사용자 연주 시간 → 악보상 위치')
plt.legend(loc='upper left', fontsize=8)
plt.tight_layout()

plt.subplot(2, 1, 2)
librosa.display.specshow(ref_chroma, x_axis=None, y_axis='chroma', hop_length=HOP, sr=SR, cmap='magma')
plt.title('참고: 정답(악보) 오디오의 크로마 특징 (12음고 에너지 분포)')
plt.tight_layout()

plt.savefig('dtw_alignment_result.png', dpi=130)
print("\n시각화 저장 완료: dtw_alignment_result.png")
