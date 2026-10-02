import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import ReferencePlayer from './ReferencePlayer';

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'https://project-m-backend-ar2l.onrender.com';

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const [songModeActive, setSongModeActive] = useState(() => {
    return localStorage.getItem('songModeActive') === 'true';
  });
  
  const [uploadResponse, setUploadResponse] = useState(() => {
    const saved = localStorage.getItem('uploadResponse');
    return saved ? JSON.parse(saved) : null;
  });
    
  const [scoreImages, setScoreImages] = useState(() => {
    const saved = localStorage.getItem('scoreImages');
    return saved ? JSON.parse(saved) : [];
  });
  
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const imageRefs = useRef([]);
  const scrollContainerRef = useRef(null);

  const [zoomLevel, setZoomLevel] = useState(100);
  const zoomIn = () => setZoomLevel((z) => Math.min(300, z + 20));
  const zoomOut = () => setZoomLevel((z) => Math.max(40, z - 20));
  const resetZoom = () => setZoomLevel(100);

  // --- 🎹 메트로놈 관련 상태 및 로직 ---
  const [bpm, setBpm] = useState(120);
  const [isMetronomeActive, setIsMetronomeActive] = useState(false);

  // --- 🎤 실시간 마이크 & 웹소켓 오토 스크롤 상태 ---
  const [isListening, setIsListening] = useState(false);
  const socketRef = useRef(null);
  const [currentPageIndex, setCurrentPageIndex] = useState(0);
  const audioContextRef = useRef(null);
  const processorRef = useRef(null);
  const sourceRef = useRef(null);
  const [currentMeasure, setCurrentMeasure] = useState(1); // 현재 감지된 마디 번호 상태

  // Web Audio API를 이용해 짧고 명확한 메트로놈 틱 소리 재생
  const playClick = () => {
    try {
      const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, audioCtx.currentTime); // 800Hz 톤
      
      gain.gain.setValueAtTime(1, audioCtx.currentTime);
      if (gain.gain.exponentialRampToValueAtTime) {
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.05);
      } else {
        gain.gain.linearRampToValueAtTime(0.001, audioCtx.currentTime + 0.05);
      }

      osc.connect(gain);
      gain.connect(audioCtx.destination);
      
      osc.start();
      osc.stop(audioCtx.currentTime + 0.05);
    } catch (e) {
      console.error('메트로놈 오디오 재생 오류:', e);
    }
  };

  useEffect(() => {
    let interval = null;
    if (isMetronomeActive) {
      const intervalTime = (60 / bpm) * 1000;
      interval = setInterval(() => {
        playClick();
      }, intervalTime);
    } else {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isMetronomeActive, bpm]);

  const handleBpmChange = (e) => {
    const val = parseInt(e.target.value, 10);
    if (isNaN(val)) {
      setBpm(60);
    } else {
      setBpm(Math.max(40, Math.min(240, val)));
    }
  };

  const [viewportSize, setViewportSize] = useState({ w: window.innerWidth, h: window.innerHeight });
  useEffect(() => {
    const onResize = () => setViewportSize({ w: window.innerWidth, h: window.innerHeight });
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const [naturalSizes, setNaturalSizes] = useState({});
  const imgElRefs = useRef({});

  const recordNaturalSize = (index, imgEl) => {
    if (!imgEl || !imgEl.naturalWidth) return;
    setNaturalSizes((prev) => {
      if (prev[index] && prev[index].w === imgEl.naturalWidth && prev[index].h === imgEl.naturalHeight) {
        return prev;
      }
      return { ...prev, [index]: { w: imgEl.naturalWidth, h: imgEl.naturalHeight } };
    });
  };

  const handleImageLoad = (index, e) => recordNaturalSize(index, e.target);

  useEffect(() => {
    scoreImages.forEach((_, index) => {
      const el = imgElRefs.current[index];
      if (el && el.complete) recordNaturalSize(index, el);
    });
  }, [scoreImages]);

  const getRenderedSize = (index) => {
    const nat = naturalSizes[index];
    if (!nat) return null;
    const maxW = viewportSize.w * 0.85;
    const maxH = viewportSize.h - 180;
    
    const scaleW = maxW / nat.w;
    const scaleH = maxH / nat.h;
    const baseScale = Math.min(scaleW, scaleH); 

    const zoomFactor = zoomLevel / 100;
    const finalScale = baseScale * zoomFactor;

    return {
      width: Math.round(nat.w * finalScale),
      height: Math.round(nat.h * finalScale),
    };
  };

  // 드로잉(필기/형광펜) 관련 상태
  const [isDrawingMode, setIsDrawingMode] = useState(false); 
  const [penColor, setPenColor] = useState('#ff4444'); 
  const [penWidth, setPenWidth] = useState(3); 
  const [tool, setTool] = useState('pen');
  const [highlighterOpacity, setHighlighterOpacity] = useState(0.3);
  
  const canvasRefs = useRef({}); 

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleUpload = async (fileToUpload) => {
    const targetFile = fileToUpload || selectedFile;
    if (!targetFile) {
      alert('파일을 먼저 선택해주세요!');
      return;
    }

    const formData = new FormData();
    formData.append('file', targetFile);

    setLoading(true);

    try {
      const response = await axios.post(`${BACKEND_URL}/api/score/upload`, formData, {
        headers: {
          'ngrok-skip-browser-warning': 'true',
        },
      });

      console.log('업로드 및 분석 성공:', response.data);
      
      const newResponse = response.data;
      const newImages = newResponse.sequence_data;

      setUploadResponse(newResponse);
      setScoreImages(newImages);
      setSongModeActive(true);
      imageRefs.current = new Array(newImages.length);

      localStorage.setItem('songModeActive', 'true');
      localStorage.setItem('uploadResponse', JSON.stringify(newResponse));
      localStorage.setItem('scoreImages', JSON.stringify(newImages));

    } catch (error) {
      console.error('업로드 실패:', error);
      alert('악보 처리 중 오류가 발생했습니다. 백엔드 서버 상태와 파일 형식을 확인하세요.');
    } finally {
      setLoading(false);
    }
  };

  const scrollToPage = (index) => {
    if (imageRefs.current[index]) {
      imageRefs.current[index].scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  useEffect(() => {
    if (!songModeActive) return;

    scoreImages.forEach((_, index) => {
      const canvas = canvasRefs.current[index];
      const img = imageRefs.current[index];
      if (!canvas || !img) return;

      const ctx = canvas.getContext('2d');
      
      const updateCanvasSize = () => {
        canvas.width = img.naturalWidth || img.width;
        canvas.height = img.naturalHeight || img.height;
      };

      if (img.complete) {
        updateCanvasSize();
      } else {
        img.onload = updateCanvasSize;
      }

      let isDrawing = false;

      const startDrawing = (e) => {
        if (!isDrawingMode) return;
        isDrawing = true;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        
        ctx.beginPath();
        ctx.moveTo((e.clientX - rect.left) * scaleX, (e.clientY - rect.top) * scaleY);
      };

      const draw = (e) => {
        if (!isDrawing || !isDrawingMode) return;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;

        ctx.lineTo((e.clientX - rect.left) * scaleX, (e.clientY - rect.top) * scaleY);
        if (tool === 'eraser') {
          ctx.globalCompositeOperation = 'destination-out';
          ctx.lineWidth = 15; 
          ctx.globalAlpha = 1.0;
        } else if (tool === 'highlighter') {
          ctx.globalCompositeOperation = 'multiply';
          ctx.strokeStyle = penColor;
          ctx.lineWidth = 12; 
          ctx.globalAlpha = highlighterOpacity; 
        } else {
          ctx.globalCompositeOperation = 'source-over';
          ctx.strokeStyle = penColor;
          ctx.lineWidth = penWidth; 
          ctx.globalAlpha = 1.0; 
        } 

        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        ctx.stroke();
      };

      const stopDrawing = () => {
        if (!isDrawing) return;
        isDrawing = false;
        ctx.beginPath();
      };

      canvas.onmousedown = startDrawing;
      canvas.onmousemove = draw;
      canvas.onmouseup = stopDrawing;
      canvas.onmouseleave = stopDrawing;
    });
  }, [songModeActive, scoreImages, isDrawingMode, penColor, penWidth, tool, highlighterOpacity]);

  const startLiveSync = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const wsProtocol = BACKEND_URL.startsWith('https') ? 'wss' : 'ws';
      const wsHost = BACKEND_URL.replace(/^https?:\/\//, '');
      const ws = new WebSocket(`${wsProtocol}://${wsHost}/ws/audio-sync`);
      socketRef.current = ws;

      ws.onopen = () => {
        console.log('백엔드 오디오 웹소켓 연결 완료');
        const filename = uploadResponse?.filename || '';
        ws.send(JSON.stringify({ filename: filename }));
        setIsListening(true);
        alert('실시간 연주 감지가 시작되었습니다!');
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.measure) {
          setCurrentMeasure(data.measure);
        }
      };

      ws.onclose = () => {
        stopLiveSync();
      };

      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      const audioCtx = new AudioContextClass({ sampleRate: 22050 });
      audioContextRef.current = audioCtx;

      const source = audioCtx.createMediaStreamSource(stream);
      sourceRef.current = source;

      const processor = audioCtx.createScriptProcessor(4096, 1, 1);
      processorRef.current = processor;

      processor.onaudioprocess = (e) => {
        if (ws.readyState === WebSocket.OPEN) {
          const inputData = e.inputBuffer.getChannelData(0);
          ws.send(inputData.buffer);
        }
      };

      source.connect(processor);
      processor.connect(audioCtx.destination);

    } catch (err) {
      console.error('마이크 연결 실패:', err);
      alert('마이크 접근 권한을 확인해주세요.');
      setIsListening(false);
    }
  };

  const stopLiveSync = () => {
    if (processorRef.current && audioContextRef.current) {
      processorRef.current.disconnect();
      sourceRef.current?.disconnect();
      audioContextRef.current.close();
      processorRef.current = null;
      audioContextRef.current = null;
      sourceRef.current = null;
    }

    if (socketRef.current) {
      socketRef.current.close();
      socketRef.current = null;
    }

    setIsListening(false);
  };

  useEffect(() => {
    if (!isListening || !currentMeasure) return;
    const MEASURES_PER_PAGE = 8;
    const pageIndex = Math.floor((currentMeasure - 1) / MEASURES_PER_PAGE);

    if (pageIndex >= 0 && pageIndex < scoreImages.length) {
      scrollToPage(pageIndex);
    }
  }, [currentMeasure, isListening, scoreImages.length]);

  return (
    <div style={{ padding: '0px', fontFamily: 'Arial, sans-serif', height: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: '#121212', color: 'white' }}>
      
      {/* 헤더 */}
      <header style={{ backgroundColor: '#1e1e1e', padding: '12px 20px', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {songModeActive && (
                <button 
                    onClick={() => setSidebarOpen(!sidebarOpen)} 
                    style={{ padding: '6px 12px', backgroundColor: '#333', color: 'white', border: '1px solid #555', borderRadius: '4px', cursor: 'pointer', fontSize: '13px' }}
                >
                    {sidebarOpen ? '📁 사이드바 닫기' : '📂 사이드바 열기'}
                </button>
            )}
        </div>
        
        <h2 style={{ margin: 0, fontSize: '18px' }}>🎹 AI 스마트 음악 레슨 조수</h2>
        
        <div style={{ display: 'flex', gap: '10px' }}>
            {songModeActive && (
                <>
                  <input 
                    type="file" 
                    id="new-score-upload" 
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        handleUpload(e.target.files[0]);
                      }
                    }} 
                    accept=".pdf,.png,.jpg,.jpeg" 
                    style={{ display: 'none' }} 
                  />
                  <label 
                    htmlFor="new-score-upload" 
                    style={{ padding: '6px 12px', backgroundColor: '#2196F3', color: 'white', borderRadius: '4px', cursor: 'pointer', fontSize: '13px', display: 'flex', alignItems: 'center' }}
                  >
                    📄 새 악보 업로드
                  </label>
                </>
            )}
        </div>
      </header>

      {/* 메인 컨텐츠 영역 */}
      <main style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>
        
        {!songModeActive ? (
          /* 최초 업로드 화면 */
          <div style={{ width: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <div style={{ border: '2px dashed #555', padding: '40px', textAlign: 'center', borderRadius: '12px', backgroundColor: '#1e1e1e', maxWidth: '500px', width: '100%' }}>
                <h3 style={{ marginTop: 0 }}>연습할 악보(PDF/이미지)를 업로드하세요</h3>
                <p style={{ color: '#aaa', fontSize: '14px', marginBottom: '20px' }}>지원 형식: PDF (.pdf), 이미지 (.png, .jpg)</p>
                <input type="file" onChange={handleFileChange} accept=".pdf,.png,.jpg,.jpeg" style={{ margin: '15px 0', display: 'block', width: '100%', padding: '10px', backgroundColor: '#333', borderRadius: '4px' }} />
                <button 
                  onClick={() => handleUpload(null)} 
                  disabled={loading}
                  style={{ padding: '12px 24px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold', width: '100%' }}
                >
                  {loading ? '업로드 및 악보 변환 중...' : '업로드 및 연습 시작'}
                </button>
            </div>
          </div>
        ) : (
          /* 악보 뷰어 + 필기 모드 인터페이스 */
          <div style={{ width: '100%', height: '100%', display: 'flex', overflow: 'hidden' }}>
            
            {/* 좌측 사이드바 (페이지 목록 + 교보재 레퍼런스 플레이어) */}
            {sidebarOpen && (
              <div style={{ width: '280px', backgroundColor: '#181818', borderRight: '1px solid #333', display: 'flex', flexDirection: 'column', height: '100%', zIndex: 5 }}>
                
                {/* 스마트 교보재 레퍼런스 위젯 */}
                <div style={{ borderBottom: '1px solid #333', overflowY: 'auto' }}>
                  <ReferencePlayer 
                    filename={uploadResponse?.filename} 
                    backendUrl={BACKEND_URL}
                    currentMeasure={currentMeasure}
                  />
                </div>

                {/* 악보 페이지 목록 */}
                <div style={{ padding: '10px 15px', borderBottom: '1px solid #333', backgroundColor: '#1e1e1e' }}>
                  <span style={{ fontSize: '13px', fontWeight: 'bold', color: '#8BC34A' }}>📑 악보 페이지 ({scoreImages.length}쪽)</span>
                </div>
                <div style={{ flex: 1, overflowY: 'auto', padding: '10px' }}>
                  {scoreImages.map((_, index) => (
                    <button
                      key={index}
                      onClick={() => scrollToPage(index)}
                      style={{
                        display: 'block',
                        width: '100%',
                        padding: '10px 12px',
                        marginBottom: '6px',
                        backgroundColor: '#252525',
                        color: '#ddd',
                        border: '1px solid #333',
                        borderRadius: '4px',
                        cursor: 'pointer',
                        textAlign: 'left',
                        fontSize: '13px',
                      }}
                    >
                      📄 악보 페이지 {index + 1}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* 메인 뷰어 영역 */}
            <div style={{ flex: 1, height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden', position: 'relative' }}>
                
                {/* 상단 컨트롤 바 */}
                <div style={{ backgroundColor: '#1a1a1a', padding: '10px 20px', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '13px', flexWrap: 'wrap', gap: '12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <span style={{ color: '#8BC34A', fontWeight: 'bold' }}>📂 {uploadResponse?.filename}</span>
                  </div>

                  {/* 메트로놈 + 필기 툴바 + 실시간 감지 */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                    
                    {/* 🎵 메트로놈 */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', backgroundColor: '#252525', padding: '4px 10px', borderRadius: '6px', border: '1px solid #444' }}>
                      <span style={{ fontSize: '12px', color: '#FF9800', fontWeight: 'bold' }}>Metronome</span>
                      <button 
                        onClick={() => setBpm((prev) => Math.max(40, prev - 5))}
                        style={{ padding: '2px 6px', backgroundColor: '#333', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer', fontSize: '11px' }}
                      >
                        -
                      </button>
                      <input 
                        type="number" 
                        value={bpm} 
                        onChange={handleBpmChange}
                        style={{ width: '42px', textAlign: 'center', backgroundColor: '#111', color: '#8BC34A', border: '1px solid #444', borderRadius: '3px', fontSize: '12px', fontWeight: 'bold', padding: '2px 0' }}
                      />
                      <span style={{ fontSize: '11px', color: '#aaa' }}>BPM</span>
                      <button 
                        onClick={() => setBpm((prev) => Math.min(240, prev + 5))}
                        style={{ padding: '2px 6px', backgroundColor: '#333', color: 'white', border: 'none', borderRadius: '3px', cursor: 'pointer', fontSize: '11px' }}
                      >
                        +
                      </button>
                      <button 
                        onClick={() => setIsMetronomeActive(!isMetronomeActive)}
                        style={{ marginLeft: '4px', padding: '3px 8px', backgroundColor: isMetronomeActive ? '#d32f2f' : '#4CAF50', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' }}
                      >
                        {isMetronomeActive ? '⏹ 정지' : '▶ 시작'}
                      </button>
                    </div>

                    {/* ✏️ 펜 / 형광펜 / 지우개 툴바 */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', backgroundColor: '#252525', padding: '4px 8px', borderRadius: '6px', border: '1px solid #444' }}>
                      <button 
                        onClick={() => { setTool('pen'); setIsDrawingMode(true); }}
                        style={{ 
                          backgroundColor: tool === 'pen' && isDrawingMode ? '#2196F3' : '#333', 
                          color: 'white',
                          padding: '4px 8px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' 
                        }}
                      >
                        ✏️ 펜
                      </button>
                      <button 
                        onClick={() => { setTool('highlighter'); setIsDrawingMode(true); }}
                        style={{ 
                          backgroundColor: tool === 'highlighter' && isDrawingMode ? '#2196F3' : '#333', 
                          color: 'white',
                          padding: '4px 8px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' 
                        }}
                      >
                        🖍️ 형광펜
                      </button>
                      <button 
                        onClick={() => { setTool('eraser'); setIsDrawingMode(true); }}
                        style={{ 
                          backgroundColor: tool === 'eraser' && isDrawingMode ? '#ff5252' : '#333', 
                          color: 'white',
                          padding: '4px 8px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' 
                        }}
                      >
                        🧹 지우개
                      </button>
                      
                      {tool === 'highlighter' && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginLeft: '4px', paddingLeft: '6px', borderLeft: '1px solid #444', fontSize: '11px', color: '#aaa' }}>
                          <span>투명도: {Math.round(highlighterOpacity * 100)}%</span>
                          <input 
                            type="range" 
                            min="0.1" 
                            max="0.8" 
                            step="0.05" 
                            value={highlighterOpacity} 
                            onChange={(e) => setHighlighterOpacity(parseFloat(e.target.value))}
                            style={{ width: '55px', cursor: 'pointer' }}
                          />
                        </div>
                      )}

                      {/* 🎨 펜 및 형광펜 색상 팔레트 */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: '6px', paddingLeft: '6px', borderLeft: '1px solid #444' }}>
                        {[
                          { name: '빨강', hex: '#f50c0c' },
                          { name: '노랑', hex: '#FFEB3B' },
                          { name: '연두', hex: '#8BC34A' },
                          { name: '하늘', hex: '#03A9F4' },
                          { name: '민트', hex: '#8eebcf' },
                          { name: '주황', hex: '#FF9800' }
                        ].map((c) => (
                          <button
                            key={c.hex}
                            onClick={() => setPenColor(c.hex)}
                            title={c.name}
                            style={{
                              width: '18px',
                              height: '18px',
                              backgroundColor: c.hex,
                              border: penColor === c.hex ? '2px solid #ffffff' : '1px solid #555',
                              borderRadius: '50%',
                              cursor: 'pointer',
                              padding: '0',
                              transform: penColor === c.hex ? 'scale(1.15)' : 'scale(1)',
                              transition: 'all 0.15s ease'
                            }}
                          />
                        ))}
                      </div>

                      <button 
                        onClick={() => setIsDrawingMode(!isDrawingMode)}
                        style={{ 
                          marginLeft: '4px',
                          backgroundColor: isDrawingMode ? '#4CAF50' : '#555', 
                          color: 'white',
                          padding: '4px 8px', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '11px', fontWeight: 'bold' 
                        }}
                      >
                        {isDrawingMode ? '✍️ 필기 ON' : '🔒 필기 OFF'}
                      </button>
                    </div>

                    {/* 🎤 실시간 연주 감지 */}
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <button 
                        onClick={isListening ? stopLiveSync : startLiveSync}
                        style={{ 
                          padding: '6px 12px', 
                          backgroundColor: isListening ? '#d32f2f' : '#2196F3', 
                          color: 'white', 
                          border: 'none', 
                          borderRadius: '4px', 
                          cursor: 'pointer', 
                          fontWeight: 'bold', 
                          fontSize: '12px'
                        }}
                      >
                        {isListening ? '⏹ 감지 중지' : '🎤 실시간 연주 감지'}
                      </button>

                      {isListening && (
                        <div style={{ 
                          backgroundColor: '#333', 
                          padding: '5px 10px', 
                          borderRadius: '4px', 
                          color: '#8BC34A', 
                          fontSize: '12px', 
                          fontWeight: 'bold'
                        }}>
                          🎯 {currentMeasure}마디
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* 악보 및 캔버스 렌더링 영역 */}
                <div style={{ flex: 1, width: '100%', height: '100%', overflow: 'hidden', position: 'relative' }}>
                    {scoreImages.length > 0 ? (
                        <React.Fragment>
                            {/* 줌 컨트롤 */}
                            <div style={{ position: 'absolute', top: '10px', right: '10px', zIndex: 10, display: 'flex', gap: '5px' }}>
                                <button onClick={zoomIn} style={{ padding: '4px 8px', backgroundColor: '#333', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>+</button>
                                <button onClick={zoomOut} style={{ padding: '4px 8px', backgroundColor: '#333', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>-</button>
                                <button onClick={resetZoom} style={{ padding: '4px 8px', backgroundColor: '#333', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>초기화</button>
                                <span style={{ padding: '4px 8px', backgroundColor: '#1a1a1a', color: '#8BC34A', borderRadius: '4px', fontSize: '12px', alignSelf: 'center' }}>{zoomLevel}%</span>
                            </div>

                            {/* 악보 스크롤 컨테이너 */}
                            <div
                                ref={scrollContainerRef}
                                style={{
                                    width: '100%',
                                    height: '100%',
                                    overflowY: 'auto',
                                    overflowX: 'hidden',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    alignItems: 'center',
                                    paddingBottom: '60px',
                                }}
                            >
                                {scoreImages.map((imgPath, index) => {
                                    const renderedSize = getRenderedSize(index);
                                    return (
                                    <div
                                        key={index}
                                        ref={(el) => (imageRefs.current[index] = el)}
                                        style={{
                                            width: '100%',
                                            display: 'flex',
                                            flexDirection: 'column',
                                            alignItems: 'center',
                                            padding: '25px 0',
                                            boxSizing: 'border-box',
                                            borderBottom: '2px solid #333',
                                        }}
                                    >
                                        <div style={{ color: '#888', fontSize: '12px', marginBottom: '8px', letterSpacing: '1px' }}>
                                            — 악보 페이지 {index + 1} / {scoreImages.length} —
                                        </div>
                                        <div
                                            style={{
                                                position: 'relative',
                                                display: 'inline-block',
                                                boxShadow: '0 4px 15px rgba(0,0,0,0.7)',
                                            }}
                                        >
                                            <img
                                                src={`${BACKEND_URL}/${imgPath}`}
                                                alt={`악보 페이지 ${index + 1}`}
                                                ref={(el) => { imgElRefs.current[index] = el; }}
                                                onLoad={(e) => handleImageLoad(index, e)}
                                                style={
                                                    renderedSize
                                                        ? {
                                                              width: `${renderedSize.width}px`,
                                                              height: `${renderedSize.height}px`,
                                                              display: 'block',
                                                              border: '1px solid #444',
                                                          }
                                                        : {
                                                              maxWidth: '85vw',
                                                              maxHeight: 'calc(100vh - 200px)',
                                                              width: 'auto',
                                                              height: 'auto',
                                                              display: 'block',
                                                              border: '1px solid #444',
                                                          }
                                                }
                                            />
                                            {/* 악보 필기용 캔버스 */}
                                            <canvas
                                                ref={(el) => (canvasRefs.current[index] = el)}
                                                style={{
                                                    position: 'absolute',
                                                    top: 0,
                                                    left: 0,
                                                    width: '100%',
                                                    height: '100%',
                                                    mixBlendMode: 'multiply',
                                                    pointerEvents: isDrawingMode ? 'auto' : 'none',
                                                }}
                                            />
                                        </div>
                                    </div>
                                    );
                                })}
                            </div>
                        </React.Fragment>
                    ) : (
                        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', color: '#888' }}>
                            악보 이미지를 불러오는 중입니다...
                        </div>
                    )}
                </div>
                
                <div style={{ backgroundColor: '#1e1e1e', padding: '10px', borderTop: '1px solid #333', textAlign: 'center' }}>
                    <p style={{ margin: '0', color: '#aaa', fontSize: '13px' }}>🎤 마이크를 켜고 연주를 시작하면 악보가 자동으로 동기화됩니다.</p>
                </div>
            </div>

          </div>
        )}
      </main>
    </div>
  );
}

export default App;