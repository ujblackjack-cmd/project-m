"""
1단계: 테스트용 피아노 악보 생성
- 저작권 문제 없는 짧은 오리지널 멜로디+화음 (16마디, 4/4박자, C major)
- MusicXML과 MIDI 둘 다 저장 (MusicXML은 '악보', MIDI는 '정답 오디오 합성용')
"""
from music21 import stream, note, chord, meter, tempo, key, metadata

s = stream.Part(id='piano')
s.append(metadata.Metadata())
s.append(meter.TimeSignature('4/4'))
s.append(key.KeySignature(0))  # C major
s.append(tempo.MetronomeMark(number=96))

# 오른손 멜로디 + 왼손 화음을 한 파트에 순차 배치 (프로토타입 단순화)
melody = ['C4','D4','E4','F4','G4','A4','G4','F4',
          'E4','D4','C4','D4','E4','C4','G3','C4']
chords = [['C3','E3','G3'], None, None, None,
          ['F3','A3','C4'], None, None, None,
          ['G3','B3','D4'], None, None, None,
          ['C3','E3','G3'], None, None, None]

measure_num = 1
for i in range(0, len(melody), 4):
    m = stream.Measure(number=measure_num)
    for j in range(4):
        idx = i + j
        n = note.Note(melody[idx], quarterLength=1.0)
        m.append(n)
    s.append(m)
    measure_num += 1

score_obj = stream.Score()
score_obj.insert(0, s)

score_obj.write('musicxml', fp='piano_test_score.musicxml')
score_obj.write('midi', fp='piano_test_score.mid')

# 마디별 시작 시각(초, 96bpm 기준) 매핑도 저장해둔다 -> 나중에 "지금 몇 마디인지" 계산용
sec_per_beat = 60.0 / 96
measures_info = []
for i, m_start_beat in enumerate(range(0, len(melody), 4)):
    measures_info.append({
        'measure': i + 1,
        'start_beat': m_start_beat,
        'start_sec': m_start_beat * sec_per_beat
    })

import json
with open('measures_info.json', 'w') as f:
    json.dump(measures_info, f, indent=2)

print("악보 생성 완료: piano_test_score.musicxml / piano_test_score.mid")
print(f"총 마디 수: {measure_num - 1}, 템포: 96bpm")
for m in measures_info:
    print(m)
