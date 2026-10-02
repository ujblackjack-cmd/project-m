import React, { useRef, useState, useEffect } from 'react';
import axios from 'axios';

export default function ReferencePlayer({ filename, backendUrl, currentMeasure }) {
  const videoRef = useRef(null);
  const [videoUrl, setVideoUrl] = useState('');
  const [timestamps, setTimestamps] = useState({});
  const [inputUrl, setInputUrl] = useState('');

  // 백엔드에서 정보 가져오기
  useEffect(() => {
    if (!filename) return;
    axios.get(`${backendUrl}/api/reference/${filename}`)
      .then(res => {
        if (res.data.video_url) {
          setVideoUrl(res.data.video_url);
          setInputUrl(res.data.video_url);
        }
        if (res.data.measure_timestamps) {
          setTimestamps(res.data.measure_timestamps);
        }
      })
      .catch(err => console.error("교보재 정보 로드 실패:", err));
  }, [filename, backendUrl]);

  //특정 타임스탬프(초)로 이동
  const seekToTime = (seconds) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      videoRef.current.play();
    }
  };

  //영상 URL 등록
  const handleSaveUrl = async () => {
    try {
      await axios.post(`${backendUrl}/api/reference`, {
        filename,
        video_url: inputUrl,
        measure_timestamps: timestamps
      });
      setVideoUrl(inputUrl);
      alert("참고 영상이 저장되었습니다.");
    } catch (err) {
      alert("저장 실패");
    }
  };

  return (
    <div style={{ padding: '15px', backgroundColor: '#222', borderRadius: '8px', color: 'white' }}>
      <h4 style={{ margin: '0 0 10px 0', color: '#FF9800' }}>🎥 스마트 교보재 (참고 영상)</h4>
      
      {/* URL 입력란 */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '10px' }}>
        <input 
          type="text" 
          placeholder="영상 URL (.mp4 또는 웹 링크)"
          value={inputUrl}
          onChange={(e) => setInputUrl(e.target.value)}
          style={{ flex: 1, padding: '6px', borderRadius: '4px', border: '1px solid #444', backgroundColor: '#111', color: 'white', fontSize: '12px' }}
        />
        <button onClick={handleSaveUrl} style={{ padding: '6px 12px', backgroundColor: '#2196F3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '12px' }}>
          저장
        </button>
      </div>

      {/* 비디오 플레이어 */}
      {videoUrl ? (
        <video 
          ref={videoRef} 
          src={videoUrl} 
          controls 
          style={{ width: '100%', borderRadius: '6px', maxHeight: '200px', backgroundColor: '#000' }}
        />
      ) : (
        <p style={{ fontSize: '12px', color: '#888' }}>등록된 참고 영상이 없습니다.</p>
      )}

      {/* 마디 이동 퀵 버튼 목록 */}
      <div style={{ marginTop: '10px' }}>
        <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '6px' }}>📍 마디로 바로 이동:</div>
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
          {Object.entries(timestamps).map(([measure, sec]) => (
            <button
              key={measure}
              onClick={() => seekToTime(sec)}
              style={{
                padding: '4px 8px',
                backgroundColor: currentMeasure === parseInt(measure) ? '#FF9800' : '#444',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '11px'
              }}
            >
              {measure}마디 ({sec}초)
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}