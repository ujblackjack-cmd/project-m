"""
마이크 장치 진단용 스크립트.
'python check_devices.py' 로 실행해서 어떤 오디오 장치가 잡히는지 확인한다.
"""
import sounddevice as sd

print("=== 사용 가능한 오디오 장치 목록 ===")
print(sd.query_devices())

print("\n=== 기본 입력 장치 ===")
try:
    default_input = sd.query_devices(kind='input')
    print(default_input)
except Exception as e:
    print("기본 입력 장치를 찾을 수 없습니다:", e)

print("\n=== 기본 장치 인덱스 (sd.default.device) ===")
print(sd.default.device)
