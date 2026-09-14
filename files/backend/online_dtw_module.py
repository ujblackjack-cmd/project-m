"""
4단계: Online DTW (실시간 악보 추적) 핵심 엔진

지난 프로토타입(03_align_and_track.py)의 배치 DTW는 '연주가 다 끝난 뒤' 전체를
한번에 정렬했다. 실서비스에서는 연주 중간중간 매 프레임(약 20~30ms)마다
"지금 어디를 연주 중인가"를 그 순간까지 들어온 데이터만으로 답해야 한다.
(미래의 오디오를 미리 볼 수 없음 = causal 처리)

이 스크립트는 Dixon(2005)의 OLTW(On-Line Time Warping) 아이디어를 단순화한
'윈도우 기반 인과적(causal) DTW'를 구현한다:

- 악보(정답) 쪽 특징은 미리 다 알고 있음 (사전 렌더링된 정답 오디오에서 추출)
- 실제 연주(쿼리) 쪽 특징은 한 프레임씩 실시간으로 들어온다고 가정
- 매 프레임이 들어올 때마다, "현재 추정 위치" 주변 윈도우(예: ±3초)만 계산해서
  누적 비용이 최소인 지점을 다음 추정 위치로 갱신 -> 이러면 계산량이 작아서 실시간 가능
- 계산에 쓰는 것은 '지금까지 들어온 연주 프레임'뿐이라 완전히 인과적(causal)이다.

실제 Dixon(2005) 논문은 이보다 더 정교하게(Row/Column 진행 방향을 스텝별로 선택,
MaxRunCount로 한쪽으로 쏠리는 것 방지 등) 처리하지만, 이 단순화 버전으로도
'실시간으로 프레임 단위 추정이 가능하다'는 핵심 원리는 동일하게 검증할 수 있다.
"""

import numpy as np


class OnlineDTW:
    def __init__(self, ref_features, window_sec=3.0, hop_sec=512 / 22050, cost_metric="cosine"):
        """
        ref_features: (n_features, n_ref_frames) 형태의 정답(악보) 특징 행렬. 미리 전부 계산되어 있음.
        window_sec: 현재 추정 위치 기준 앞뒤로 몇 초까지 탐색할지 (탐색 윈도우 폭)
        hop_sec: 프레임 하나가 차지하는 시간(초). 윈도우를 프레임 수로 환산하는 데 사용.
        """
        self.ref = ref_features / (np.linalg.norm(ref_features, axis=0, keepdims=True) + 1e-8)
        self.n_ref = ref_features.shape[1]
        self.window = int(window_sec / hop_sec)
        self.cost_metric = cost_metric

        self.j_est = 0          # 현재 추정하는 '악보상' 프레임 위치
        self.i = 0              # 지금까지 받은 '연주' 프레임 개수
        # 누적 비용을 저장할 배열 (전체를 다 저장하진 않고, 지금까지 온 연주 프레임 수만큼만 늘어남)
        self.D_prev_row = None  # 직전 연주 프레임(i-1)에서의 누적비용 (윈도우 범위)
        self.prev_window_range = None
        self.history = []       # (연주 프레임 인덱스, 추정된 악보 프레임 인덱스) 기록

    def _cost(self, live_vec, ref_idx_range):
        """live_vec(현재 연주 프레임 특징)과 ref_idx_range 구간의 정답 특징들 간 코사인 거리"""
        live_n = live_vec / (np.linalg.norm(live_vec) + 1e-8)
        ref_slice = self.ref[:, ref_idx_range]
        sims = live_n @ ref_slice  # cosine similarity
        return 1 - sims  # distance

    def step(self, live_feature_vec):
        """
        실시간으로 연주 프레임이 하나 들어올 때마다 호출.
        live_feature_vec: (n_features,) 현재 순간의 크로마 벡터
        반환: 이번 프레임에서 추정된 악보(정답) 프레임 인덱스
        """
        lo = max(0, self.j_est - self.window)
        hi = min(self.n_ref, self.j_est + self.window + 1)
        ref_range = np.arange(lo, hi)

        cost_now = self._cost(live_feature_vec, ref_range)  # 이번 프레임 vs 윈도우 내 각 정답 프레임의 거리

        if self.D_prev_row is None:
            # 첫 프레임: 이전 누적비용이 없으므로 그 자체가 누적비용
            D_now = cost_now.copy()
        else:
            # 이전 스텝의 누적비용(D_prev_row, prev_window_range에 대응)을 현재 윈도우에 맞춰 정렬한 뒤
            # DTW 재귀식 D[i,j] = cost(i,j) + min(D[i-1,j], D[i,j-1], D[i-1,j-1]) 을
            # '윈도우 내에서, j 방향으로만' 근사 적용 (i-1행 전체를 유지하지 않는 스트리밍 근사)
            D_now = np.empty_like(cost_now)
            prev_lo = self.prev_window_range[0]
            for k, j in enumerate(ref_range):
                # D[i-1, j] : 직전 프레임의 같은 j 위치 누적비용 (창 밖이면 큰 값)
                idx_prev = j - prev_lo
                d_diag = self.D_prev_row[idx_prev - 1] if 0 <= idx_prev - 1 < len(self.D_prev_row) else np.inf
                d_up = self.D_prev_row[idx_prev] if 0 <= idx_prev < len(self.D_prev_row) else np.inf
                d_left = D_now[k - 1] if k > 0 else np.inf
                # 버그 수정: 세 후보(diag/up/left)가 전부 이력이 없는(inf) 경우 "0"으로 취급하면
                # 누적비용이 쌓인 정상 경로보다 '이력이 아예 없는 새 지점'이 항상 더 싸 보이는
                # 착시가 생겨, 시간이 지날수록 알고리즘이 엉뚱한 곳(주로 윈도우 가장자리)으로
                # 튀어버리는 치명적 버그가 됨. 이력이 없으면 큰 페널티를 줘서
                # "실제로 이어지는 경로"가 항상 우선되도록 한다.
                NO_HISTORY_PENALTY = 1e6
                best_prev = min(d_diag, d_up, d_left)
                if np.isinf(best_prev):
                    best_prev = NO_HISTORY_PENALTY
                D_now[k] = cost_now[k] + best_prev

        # 이번 프레임의 최적 위치 = 누적비용이 최소인 지점
        best_k = int(np.argmin(D_now))
        self.j_est = ref_range[best_k]

        self.D_prev_row = D_now
        self.prev_window_range = ref_range
        self.i += 1
        self.history.append((self.i - 1, self.j_est))
        return self.j_est
