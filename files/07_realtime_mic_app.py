"""
6단계: 실제 마이크 연동 앱 (로컬 PC에서 실행)

★ 이 스크립트는 샌드박스가 아니라 사용자의 실제 컴퓨터(마이크가 연결된 환경)에서
  실행해야 합니다. 지금까지 검증한 OnlineDTW 엔진 + 실제 마이크 입력을 연결하고,
  자동 페이지 넘김 트리거와 메트로놈까지 하나로 합친 최소 기능 데모입니다.

설치:
    pip install sounddevice librosa numpy

실행:
    python 07_realtime_mic_app.py

주의:
- 이 코드는 piano_test_score.mid로 만든 reference_audio.wav를 기준(정답)으로 사용합니다.
  실제 다른 곡으로 테스트하려면 01_make_score.py 로직을 참고해 그 곡의 reference_audio.wav와
  measures_info.json을 새로 만들어야 합니다.
- 마이크 환경(잔향, 배경 소음)에 따라 정확도가 달라질 수 있습니다. README의 한계 참고.
"""

import numpy as np
import sounddevice as sd
import librosa
import json
import threading
import time
import queue

from online_dtw_module import OnlineDTW

SR = 22050
HOP = 512
HOP_SEC = HOP / SR
BLOCK_SIZE = HOP  # 콜백이 호출되는 오디오 블록 크기 = 프레임 하나

# ---------- 1) 정답(악보) 특징 준비 ----------
print("정답 오디오에서 크로마 특징 추출 중...")
ref_y, _ = librosa.load("reference_audio.wav", sr=SR)
ref_chroma = librosa.feature.chroma_cqt(y=ref_y, sr=SR, hop_length=HOP)

with open("measures_info.json") as f:
    measures_info = json.load(f)


def ref_time_to_measure(ref_t):
    current = measures_info[0]["measure"]
    for m in measures_info:
        if ref_t >= m["start_sec"]:
            current = m["measure"]
        else:
            break
    return current


tracker = OnlineDTW(ref_chroma, window_sec=1.2, hop_sec=HOP_SEC)


def find_input_device():
    """기본 입력 장치가 설정되어 있지 않은 환경(Windows에서 흔함)을 위해
    입력 채널이 있는 장치를 자동으로 찾는다. '마이크'가 이름에 들어간
    장치를 우선하고, 없으면 입력 채널이 1개 이상인 첫 장치를 사용한다."""
    devices = sd.query_devices()
    mic_candidates = [i for i, d in enumerate(devices)
                       if d['max_input_channels'] > 0 and ('mic' in d['name'].lower() or '마이크' in d['name'])]
    if mic_candidates:
        return mic_candidates[0]
    any_input = [i for i, d in enumerate(devices) if d['max_input_channels'] > 0]
    if any_input:
        return any_input[0]
    raise RuntimeError(
        "입력 가능한 오디오 장치를 하나도 찾지 못했습니다. "
        "Windows 설정 > 개인정보 보호 > 마이크에서 '데스크톱 앱이 마이크에 "
        "액세스하도록 허용'이 켜져 있는지 확인해주세요."
    )

# ---------- 2) 메트로놈 (별도 스레드, 악보 BPM 기준 고정 박자) ----------
METRONOME_BPM = 96  # 01_make_score.py에서 설정한 템포와 동일하게 맞춤
metronome_on = threading.Event()
metronome_on.set()


def metronome_loop():
    """고정 템포로 클릭음 재생. sounddevice로 짧은 비프음을 직접 합성해서 재생한다."""
    click = (0.3 * np.sin(2 * np.pi * 1000 * np.arange(int(SR * 0.03)) / SR)).astype(np.float32)
    interval = 60.0 / METRONOME_BPM
    next_time = time.time()
    while True:
        if metronome_on.is_set():
            sd.play(click, SR)
        next_time += interval
        sleep_time = next_time - time.time()
        if sleep_time > 0:
            time.sleep(sleep_time)


# ---------- 3) 실시간 오디오 콜백: 마이크 입력 -> 크로마 -> OnlineDTW ----------
audio_buffer = np.zeros(4096, dtype=np.float32)  # 크로마 계산에 필요한 최소 길이 확보용 rolling buffer
last_measure = [None]
frame_count = [0]
stream_native_sr = [SR]  # 실제 장치가 SR을 지원 안 하면 여기에 대체 샘플레이트가 들어감


def audio_callback(indata, frames, time_info, status):
    global audio_buffer
    if status:
        print("오디오 상태 경고:", status)

    mono = indata[:, 0]
    if stream_native_sr[0] != SR:
        # 장치가 22050Hz를 지원하지 않아 다른 샘플레이트로 열었을 경우, 여기서 다시 맞춰준다
        mono = librosa.resample(mono.astype(np.float32), orig_sr=stream_native_sr[0], target_sr=SR)
    audio_buffer = np.concatenate([audio_buffer, mono])[-4096:]  # 최근 4096샘플만 유지 (약 0.19초)

    # 최근 버퍼로 크로마 한 프레임 계산 (실시간 근사: 짧은 버퍼라 저음 정확도는 다소 떨어질 수 있음 -> README 한계 참고)
    chroma = librosa.feature.chroma_cqt(y=audio_buffer, sr=SR, hop_length=HOP)
    live_vec = chroma[:, -1]  # 가장 최근 프레임

    j_est = tracker.step(live_vec)
    ref_t = j_est * HOP_SEC
    measure = ref_time_to_measure(ref_t)
    frame_count[0] += 1

    if measure != last_measure[0]:
        print(f"[{time.strftime('%H:%M:%S')}] 현재 {measure}마디 진입 감지 -> 자동 페이지 넘김 트리거!")
        last_measure[0] = measure


def main():
    print(f"악보 총 {len(measures_info)}마디, 기준 템포 {METRONOME_BPM}bpm")

    device_idx = find_input_device()
    device_info = sd.query_devices(device_idx)
    print(f"입력 장치로 [{device_idx}] {device_info['name']} 사용")

    print("메트로놈 시작 + 마이크 입력 대기 중... (Ctrl+C로 종료)")
    threading.Thread(target=metronome_loop, daemon=True).start()

    try:
        stream = sd.InputStream(device=device_idx, channels=1, samplerate=SR,
                                 blocksize=BLOCK_SIZE, callback=audio_callback)
        stream_native_sr[0] = SR
    except sd.PortAudioError:
        # 장치가 22050Hz를 지원하지 않는 경우 -> 장치의 기본 샘플레이트로 재시도
        fallback_sr = int(device_info['default_samplerate'])
        print(f"{SR}Hz를 지원하지 않는 장치입니다. {fallback_sr}Hz로 재시도합니다.")
        stream_native_sr[0] = fallback_sr
        fallback_block = int(BLOCK_SIZE * fallback_sr / SR)
        stream = sd.InputStream(device=device_idx, channels=1, samplerate=fallback_sr,
                                 blocksize=fallback_block, callback=audio_callback)

    with stream:
        try:
            while True:
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\n종료합니다.")


if __name__ == "__main__":
    main()