"""
render_piano_score.py
- 기존 피아노 화음 악보(piano_test_score.musicxml)를 로드하여 
  LilyPond 형식(.ly)으로 변환합니다.
"""
from music21 import converter, environment

# 본인의 LilyPond 설치 경로에 맞게 설정
environment.set('lilypondPath', r'C:\lilypond-2.26.0\bin\lilypond.exe')

print("피아노 화음 악보(piano_test_score.musicxml) 로드 중...")
score = converter.parse('piano_test_score.musicxml')

# LilyPond 파일(.ly)로 저장
output_ly_path = 'piano_test_score.ly'
score.write('lilypond', fp=output_ly_path)

print(f"변환 완료: {output_ly_path} 파일이 생성되었습니다.")