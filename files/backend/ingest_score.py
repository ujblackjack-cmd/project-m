"""
ingest_score.py
- 사용자가 업로드한 파일(PDF, 이미지, MusicXML)의 확장자를 판별하여
  적절한 전처리를 거친 뒤 DTW/레슨 엔진용 표준 시퀀스로 변환하는 파이프라인입니다.
"""
import os
import fitz  # PyMuPDF (PDF 처리용)
from music21 import converter

def process_uploaded_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    print(f"\n[업로드 감지] 파일 처리 시작: {file_path} (형식: {ext})")
    
    if ext == '.musicxml' or ext == '.xml':
        return _handle_musicxml(file_path)
    elif ext == '.pdf':
        return _handle_pdf(file_path)
    elif ext in ['.png', '.jpg', '.jpeg']:
        return _handle_image(file_path)
    else:
        raise ValueError(f"지원하지 않는 파일 형식입니다: {ext}")

def _handle_musicxml(xml_path):
    print(" ↳ MusicXML 파일 파싱 중...")
    score = converter.parse(xml_path)
    sequence = []
    for note_or_chord in score.flatten().notesAndRests:
        if note_or_chord.isNote:
            sequence.append(note_or_chord.pitch.midi)
        elif note_or_chord.isChord:
            sequence.append([p.midi for p in note_or_chord.pitches])
    print(f" ↳ MusicXML 처리 완료! 추출된 시퀀스 개수: {len(sequence)}개")
    return sequence

def _handle_pdf(pdf_path):
    print(" ↳ PDF 파일 페이지별 이미지 변환 중...")
    doc = fitz.open(pdf_path)
    image_paths = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(dpi=150)
        img_path = f"temp_page_{page_num + 1}.png"
        pix.save(img_path)
        image_paths.append(img_path)
        print(f"   - {page_num + 1}페이지 이미지 추출 완료: {img_path}")
    
    # PDF 내 각 페이지 이미지에 대해 OMR 추론 또는 전처리 수행 (현재는 이미지 전처리 단계로 연결)
    # 추후 이 이미지들을 OMR 엔진으로 넘기게 됩니다.
    print(" ↳ PDF 페이지별 OMR/전처리 준비 완료!")
    return image_paths

def _handle_image(img_path):
    print(" ↳ 단일 악보 이미지(PNG/JPG) 감지됨. OMR 분석 파이프라인 대기 중...")
    # 이미지 전처리 및 OMR 모듈 연동 지점
    return [img_path]

if __name__ == "__main__":
    # 테스트용으로 기존에 있던 MusicXML과 PDF/이미지 시뮬레이션 실행
    # (실제 테스트를 위해 piano_test_score.musicxml을 대상으로 실행해봅니다)
    sample_sequence = process_uploaded_file("etc/piano_test_score.musicxml")
    print(f"결과 시퀀스 샘플 (처음 5개): {sample_sequence[:5]}")