"""
run_dtw_scoring.py
- 정답 악보 시퀀스와 사용자 연주 시퀀스를 DTW 알고리즘으로 비교하여
  정렬 경로(Alignment Path)와 일치도 점수를 계산합니다.
"""
import numpy as np
from run_dtw_pipeline import load_score_for_dtw

def calculate_dtw_distance(seq_ref, seq_user):
    """
    간단한 동적 시간 워핑(DTW) 거리 계산 함수
    """
    n, m = len(seq_ref), len(seq_user)
    dtw_matrix = np.zeros((n + 1, m + 1))
    
    # 초기 비용을 무한대로 설정
    for i in range(n + 1):
        dtw_matrix[i, 0] = np.inf
    for j in range(m + 1):
        dtw_matrix[0, j] = np.inf
        
    dtw_matrix[0, 0] = 0
    
    # DP(동적 계획법)를 통한 DTW 코스트 계산
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # 화음(리스트)과 단일 음(정수) 비교 처리 예외 방어
            ref_val = seq_ref[i-1]
            user_val = seq_user[j-1]
            
            # 값 비교 (단순 절대 오차 기반)
            if isinstance(ref_val, list) and isinstance(user_val, list):
                cost = abs(np.mean(ref_val) - np.mean(user_val))
            elif isinstance(ref_val, list):
                cost = abs(np.mean(ref_val) - user_val)
            elif isinstance(user_val, list):
                cost = abs(ref_val - np.mean(user_val))
            else:
                cost = abs(ref_val - user_val)
                
            dtw_matrix[i, j] = cost + min(
                dtw_matrix[i-1, j],    # 삽입 (Insertion)
                dtw_matrix[i, j-1],    # 삭제 (Deletion)
                dtw_matrix[i-1, j-1]   # 일치/교체 (Match/Mismatch)
            )
            
    return dtw_matrix[n, m], dtw_matrix

if __name__ == "__main__":
    # 1. 정답 악보 시퀀스 로드
    reference_seq = load_score_for_dtw("piano_test_score_processed.musicxml")
    
    # 2. 시뮬레이션용 사용자 연주 시퀀스 생성 (정답과 유사하지만 약간의 오차가 있는 형태)
    # 실제 서비스에서는 마이크 오디오 입력에서 추출된 MIDI 시퀀스가 들어갑니다.
    simulated_user_seq = [note + np.random.choice([-1, 0, 1]) for note in reference_seq]
    
    print(f"사용자 연주 시퀀스 개수: {len(simulated_user_seq)}개")
    
    # 3. DTW 실행
    total_distance, matrix = calculate_dtw_distance(reference_seq, simulated_user_seq)
    print(f"DTW 매칭 완료! 총 누적 오차 거리: {total_distance:.2f}")
    
    # 간단한 채점 로직 (오차 거리가 낮을수록 높은 점수)
    score_percentage = max(0, 100 - (total_distance * 2))
    print(f"채점 결과 (Score): {score_percentage:.1f}점 / 100점")