"""
score_tracking.py
- MusicXML 악보로부터 '정답 오디오'를 합성하고 기준 크로마 특징을 추출한다.
- 실시간으로 들어오는 마이크 오디오 청크를 기준 특징과 Online DTW로 정렬해서
  "지금 몇 마디를 연주 중인가"를 계속 추정한다.

이 모듈의 핵심 알고리즘(OnlineDTW)은 별도 프로토타입에서 이미 검증을 마친 것과 동일하다:
- 배치(오프라인) DTW로 원리를 먼저 검증
- 실시간 스트리밍 시뮬레이션으로 인과적(causal) 처리가 되는지 검증
- 탐색 윈도우 경계에서 "이력 없는 위치"가 부당하게 유리해지는 버그를 발견/수정
  (자세한 내용은 프로젝트 기획서의 2단계 참고)
"""
import os
import subprocess
import tempfile
import numpy as np
import librosa
from music21 import converter, tempo as m21tempo

SR = 22050
HOP = 512
HOP_SEC = HOP / SR
N_FFT = 2048

# 시스템에 설치된 사운드폰트 중 사용 가능한 것을 자동으로 찾는다
_SOUNDFONT_CANDIDATES = [
    "/usr/share/sounds/sf2/FluidR3_GM.sf2",
    "/usr/share/sounds/sf2/TimGM6mb.sf2",
    "/usr/share/sounds/sf2/default-GM.sf2",
]


def _find_soundfont():
    for p in _SOUNDFONT_CANDIDATES:
        if os.path.exists(p):
            return p
    raise RuntimeError(
        "사운드폰트를 찾을 수 없습니다. `apt-get install fluid-soundfont-gm` 로 설치해주세요."
    )


def build_reference(musicxml_path: str):
    """
    MusicXML 파일 하나로부터:
      - chroma: (12, n_frames) 기준 크로마 특징 행렬
      - measures_info: [{"measure": 1, "start_sec": 0.0}, ...] 마디별 시작 시각
      - hop_sec: 프레임 하나가 차지하는 시간(초)
    을 계산해서 반환한다. (매번 새로 계산하면 느리므로 호출하는 쪽에서 캐싱해서 쓸 것)
    """
    score = converter.parse(musicxml_path)

    # 마디별 시작 시각 계산 (악보에 표기된 템포 기준)
    mm = score.flatten().getElementsByClass(m21tempo.MetronomeMark)
    bpm = mm[0].number if len(mm) > 0 else 120
    sec_per_quarter = 60.0 / bpm

    measures_info = []
    part = score.parts[0] if score.parts else score
    for m in part.getElementsByClass('Measure'):
        offset_quarters = m.offset  # 곡 시작부터 몇 분음표만큼 지났는지
        measures_info.append({
            "measure": m.number,
            "start_sec": round(offset_quarters * sec_per_quarter, 4),
        })
    if not measures_info:
        measures_info = [{"measure": 1, "start_sec": 0.0}]

    # MIDI로 변환 후 fluidsynth로 '정답 오디오' 합성
    with tempfile.TemporaryDirectory() as tmpdir:
        midi_path = os.path.join(tmpdir, "ref.mid")
        wav_path = os.path.join(tmpdir, "ref.wav")
        score.write("midi", fp=midi_path)

        soundfont = _find_soundfont()
        result = subprocess.run(
            ["fluidsynth", "-ni", soundfont, midi_path, "-F", wav_path, "-r", str(SR)],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0 or not os.path.exists(wav_path):
            raise RuntimeError(f"fluidsynth 렌더링 실패: {result.stderr[-500:]}")

        y, _ = librosa.load(wav_path, sr=SR)
        chroma = librosa.feature.chroma_cqt(y=y, sr=SR, hop_length=HOP)

    return chroma, measures_info, HOP_SEC


class OnlineDTW:
    """
    윈도우 기반 인과적(causal) DTW. 매 프레임 현재 추정 위치 주변 윈도우만 계산해서
    실시간 처리가 가능하도록 한 버전 (배치 DTW의 실시간 근사).
    """

    def __init__(self, ref_chroma: np.ndarray, window_sec: float = 1.5, hop_sec: float = HOP_SEC):
        self.ref = ref_chroma / (np.linalg.norm(ref_chroma, axis=0, keepdims=True) + 1e-8)
        self.n_ref = ref_chroma.shape[1]
        self.window = max(1, int(window_sec / hop_sec))
        self.j_est = 0
        self.D_prev_row = None
        self.prev_lo = 0
        self.last_cost = 1.0  # 가장 최근 매칭 비용 (0=완전 일치, 신뢰도 지표로 사용)

    def step(self, live_vec: np.ndarray) -> int:
        lo = max(0, self.j_est - self.window)
        hi = min(self.n_ref, self.j_est + self.window + 1)
        ref_range = np.arange(lo, hi)

        live_n = live_vec / (np.linalg.norm(live_vec) + 1e-8)
        sims = live_n @ self.ref[:, ref_range]
        cost_now = 1 - sims

        if self.D_prev_row is None:
            D_now = cost_now.copy()
        else:
            D_now = np.empty_like(cost_now)
            NO_HISTORY_PENALTY = 1e6  # 이력 없는 위치가 부당하게 유리해지는 버그 방지 (검증 완료된 수정)
            for k, j in enumerate(ref_range):
                idx_prev = j - self.prev_lo
                d_diag = self.D_prev_row[idx_prev - 1] if 0 <= idx_prev - 1 < len(self.D_prev_row) else np.inf
                d_up = self.D_prev_row[idx_prev] if 0 <= idx_prev < len(self.D_prev_row) else np.inf
                d_left = D_now[k - 1] if k > 0 else np.inf
                best_prev = min(d_diag, d_up, d_left)
                if not np.isfinite(best_prev):
                    best_prev = NO_HISTORY_PENALTY
                D_now[k] = cost_now[k] + best_prev

        best_k = int(np.argmin(D_now))
        self.j_est = ref_range[best_k]
        self.last_cost = float(cost_now[best_k])
        self.D_prev_row = D_now
        self.prev_lo = lo
        return self.j_est


def ref_time_to_measure(ref_t: float, measures_info: list) -> int:
    current = measures_info[0]["measure"]
    for m in measures_info:
        if ref_t >= m["start_sec"]:
            current = m["measure"]
        else:
            break
    return current


class ReferenceCache:
    """MusicXML 파일별 기준 특징을 한 번만 계산하고 메모리에 캐싱 (서버 재시작 전까지 유지)"""

    def __init__(self):
        self._cache = {}

    def get(self, musicxml_path: str):
        key = os.path.abspath(musicxml_path)
        if key not in self._cache:
            print(f"[score_tracking] '{musicxml_path}' 기준 특징 새로 계산 중 (최초 1회, 시간이 좀 걸릴 수 있음)...")
            chroma, measures_info, hop_sec = build_reference(musicxml_path)
            self._cache[key] = {"chroma": chroma, "measures_info": measures_info, "hop_sec": hop_sec}
            print(f"[score_tracking] 계산 완료: {chroma.shape[1]}프레임, {len(measures_info)}마디")
        return self._cache[key]