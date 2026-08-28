"""
2단계: '사용자 연주' 시뮬레이션
실제 마이크 녹음 대신, 정답 MIDI의 타이밍을 구간별로 늘였다 줄였다 왜곡시켜서
(사람이 어떤 부분은 빨리 치고, 어떤 부분은 느리게/머뭇거리며 치는 것처럼)
'연주 오디오'를 만든다. 이렇게 하면 DTW가 실제로 템포 변화를 따라잡는지 검증할 수 있다.
"""
import pretty_midi
import numpy as np

pm = pretty_midi.PrettyMIDI('piano_test_score.mid')

# 구간별 템포 왜곡 프로파일 (시간 구간: 배속)
# 0~2.5s: 정상속도, 2.5~5s: 느리게(0.7배속=시간 1/0.7배 늘어남), 5~7.5s: 빠르게(1.3배속), 7.5~끝: 정상
warp_segments = [
    (0.0, 2.5, 1.0),
    (2.5, 5.0, 0.7),
    (5.0, 7.5, 1.35),
    (7.5, 999.0, 1.0),
]

def warp_time(t):
    """원곡 시간 t를 '연주자가 실제로 연주하는' 시간으로 변환 (누적 왜곡 적용)"""
    warped = 0.0
    remaining = t
    for seg_start, seg_end, speed in warp_segments:
        seg_len = seg_end - seg_start
        if remaining <= 0:
            break
        if t <= seg_start:
            break
        piece = min(remaining, min(t, seg_end) - seg_start) if t > seg_start else 0
        # 더 단순하게: 구간을 순서대로 소비
    # 위 방식이 헷갈리므로 아래처럼 명시적으로 재계산
    return None

# 더 명확한 구현: 누적 방식으로 다시 작성
def build_warp_function(segments):
    # segments: list of (orig_start, orig_end, speed_multiplier)
    # speed_multiplier > 1 => 연주자가 더 빨리 침(연주시간이 짧아짐)
    # speed_multiplier < 1 => 더 느리게 침(연주시간이 길어짐)
    breakpoints_orig = [0.0]
    breakpoints_perf = [0.0]
    for (s, e, spd) in segments:
        dur_orig = e - s
        dur_perf = dur_orig / spd
        breakpoints_orig.append(breakpoints_orig[-1] + dur_orig)
        breakpoints_perf.append(breakpoints_perf[-1] + dur_perf)

    def f(t):
        for i in range(len(segments)):
            if t <= breakpoints_orig[i+1] or i == len(segments) - 1:
                seg_s, seg_e, spd = segments[i]
                local = t - breakpoints_orig[i]
                return breakpoints_perf[i] + local / spd
        return t
    return f

# 마지막 구간 끝을 실제 곡 길이로 잘라줌
total_len = pm.get_end_time() + 1.0
warp_segments[-1] = (7.5, total_len, 1.0)
warp_fn = build_warp_function(warp_segments)

# 모든 노트의 시작/끝 시각을 워프 함수로 재배치
for inst in pm.instruments:
    for n in inst.notes:
        n.start = warp_fn(n.start)
        n.end = warp_fn(n.end)

pm.write('performance_simulated.mid')
print("연주 시뮬레이션 MIDI 생성 완료: performance_simulated.mid")
print("왜곡 프로파일 (원곡 구간 -> 배속):")
for s, e, spd in warp_segments:
    label = "느리게(머뭇거림)" if spd < 1 else ("빠르게(서두름)" if spd > 1 else "정상속도")
    print(f"  {s:.1f}s~{e:.1f}s : {spd}x  ({label})")
