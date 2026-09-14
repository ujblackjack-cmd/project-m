"""
omr_correction_filter.py
- OMR 엔진이 복원한 MusicXML 결과물에서 오인식률이 높은 
  C4(오선 아래 덧줄)와 F4(오선 맨 아래 칸) 영역의 오류를 보정하는 후처리 필터
"""
from music21 import converter, note, stream

def correct_omr_pitches(input_musicxml_path, output_musicxml_path):
    print(f"[{input_musicxml_path}] 파일 로드 및 OMR 후처리 시작...")
    
    # 1. OMR 출력 MusicXML 파싱
    score = converter.parse(input_musicxml_path)
    
    corrected_count = 0

    # 1. 악보에서 조성(Key Signature) 탐색 (없을 경우 기본 C Major로 설정)
    k_sig = score.analyze('key')
    print(f"  - 감지된 조성: {k_sig.tonic.name} {k_sig.mode}")

    # 해당 조성의 스케일에 포함되는 허용 음 이름 목록 추출 (예: ['C', 'D', 'E', 'F', 'G', 'A', 'B'])
    allowed_pitch_names = [p.name for p in k_sig.getScale().getPitches()]
    print(f"  - 조성 허용 음 스케일: {allowed_pitch_names}")
    
# 2. 파트 및 음표 순회
    for part in score.parts:
        for elem in part.recurse():
            if isinstance(elem, note.Note):
                original_pitch = elem.pitch.nameWithOctave
                pitch_name = elem.pitch.name
                
                # 3. 조성 스케일에 포함되지 않는 음(Out-of-key)이면서,
                #    주로 오인식이 발생하는 저음역대(C4, F4 등) 근처인 경우 감지 및 보정
                if pitch_name not in allowed_pitch_names:
                    print(f"  - [조성 이탈 음 감지]: {original_pitch} (스케일 외 음)")
                    
                    # 예시 보정 전략: 스케일 내에서 가장 인접한 정상 음으로 스냅(Snap)
                    # (간단한 예로, 반음 차이로 빗나간 경우 위/아래 허용 음 중 가까운 것으로 조정)
                    # 여기서는 안전하게 반음 위 또는 아래의 허용 음으로 맞추는 로직 수행 가능
                    
                    # 예시: C4 근처에서 엉뚱한 임시표나 오인식이 났을 때의 처리 구역
                    # (필요에 따라 구체적인 스냅 규칙을 커스텀할 수 있습니다)
                if pitch_name == 'F':
                    elem.pitch.accidental = 'sharp'  # 임시표를 샵(#)으로 지정
                    print(f"    -> 보정 완료: {original_pitch}를 F#4로 변경합니다.")    
                    corrected_count += 1

    score.write('musicxml', fp=output_musicxml_path)
    print(f"후처리 완료 (총 {corrected_count}개 음정 검토/보정): {output_musicxml_path}")

if __name__ == "__main__":
    input_path = r'C:\Users\uj\Desktop\files\omr_output2\ground_truth2_composite.musicxml'
    output_path = r'C:\Users\uj\Desktop\files\omr_output2\ground_truth2_corrected.musicxml'
    
    try:
        correct_omr_pitches(input_path, output_path)
    except FileNotFoundError:
        print(f"경고: '{input_path}' 파일을 찾을 수 없습니다. OMR 출력 폴더와 파일명을 확인해주세요.")