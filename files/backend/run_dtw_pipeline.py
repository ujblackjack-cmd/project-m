"""
run_dtw_pipeline.py
- 후처리된 피아노 화음 MusicXML을 읽어들여 
  DTW(Score Following) 엔진과 연동하는 파이프라인 테스트 스크립트입니다.
"""
from music21 import converter

def load_score_for_dtw(xml_path):
    print(f"DTW 엔진 입력용 MusicXML 로드 중: {xml_path}")
    score = converter.parse(xml_path)
    
    # 악보에서 음정 및 박자 시퀀스 추출 (DTW 비교용 피처 추출)
    sequence = []
    for note_or_chord in score.flatten().notesAndRests:
        if note_or_chord.isNote:
            sequence.append(note_or_chord.pitch.midi)
        elif note_or_chord.isChord:
            # 화음의 경우 구성음들의 MIDI 번호 리스트 추가
            sequence.append([p.midi for p in note_or_chord.pitches])
            
    print(f"추출된 악보 시퀀스 개수: {len(sequence)}개")
    return sequence

if __name__ == "__main__":
    dtw_input_sequence = load_score_for_dtw("piano_test_score_processed.musicxml")
    print("DTW 연동 준비 완료! 실시간 연주 비교 모듈과 연결할 수 있습니다.")