"""
좀 더 현실적인 분량(24마디, 여러 줄로 자동 개행)의 단선율 악보를 생성.
실제 스캔된 악보처럼 여러 시스템(줄)에 걸쳐 표시되어야 OMR 모델이
정상적으로 오선을 그룹핑할 수 있다 (한 줄짜리+거대한 여백은 비정상 입력으로 인식됨).
"""
import random
from music21 import environment,stream, note, meter, tempo, key, metadata
environment.set('lilypondPath', r'C:\lilypond-2.26.0\bin\lilypond.exe')

random.seed(42)
pitches = ['C4','D4','E4','F4','G4','A4','B4','C5','D5']

s = stream.Part(id='melody')
s.append(meter.TimeSignature('4/4'))
s.append(key.KeySignature(0))
s.append(tempo.MetronomeMark(number=100))

measure_num = 1
all_notes = []
for _ in range(24):
    m = stream.Measure(number=measure_num)
    for _ in range(4):
        p = random.choice(pitches)
        n = note.Note(p, quarterLength=1.0)
        m.append(n)
        all_notes.append(p)
    s.append(m)
    measure_num += 1

sc = stream.Score()
sc.insert(0, s)
sc.write('musicxml', fp='ground_truth2.musicxml')
sc.write('lilypond', fp='ground_truth2.ly')
print(f"총 {measure_num-1}마디 생성 완료, 총 음표 수: {len(all_notes)}")
with open('ground_truth2_notes.txt', 'w') as f:
    f.write(','.join(all_notes))
