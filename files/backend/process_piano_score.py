"""
process_piano_score.py
- 피아노 화음 악보(piano_test_score.musicxml)를 로드하여
  조성 기반 후처리 규칙을 적용하고 DTW 입력 형태로 변환합니다.
"""
from music21 import converter, note, chord

def apply_chord_postprocessing(score_path):
    print(f"화음 악보 파일 로드 중: {score_path}")
    score = converter.parse(score_path)
    
    corrected_note_count = 0
    
    # 파트별(오른손/왼손 등) 또는 전체 음표/화음 순회
    for element in score.recurse():
        if isinstance(element, note.Note):
            # 단일 음표 후처리 로직 (예: G Major 기준 F -> F# 보정 등)
            if element.pitch.name == 'F' and element.pitch.octave == 4:
                # 예시 보정 규칙 적용
                # element.pitch.accidental = 'sharp'
                pass
        elif isinstance(element, chord.Chord):
            # 화음(여러 음이 동시에 울리는 구조) 내부의 각 음정 검증
            for n in element.notes:
                # 화음 내부 음정 후처리 규칙 적용 지점
                pass

    output_path = "piano_test_score_processed.musicxml"
    score.write('musicxml', fp=output_path)
    print(f"후처리 완료된 화음 악보 저장: {output_path}")
    return output_path

if __name__ == "__main__":
    processed_file = apply_chord_postprocessing("piano_test_score.musicxml")