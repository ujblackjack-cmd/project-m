import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function AiTutorPanel({ filename, backendUrl, currentMeasure, onSaveHistory}) {
  const [coaching, setCoaching] = useState('');
  const [loading, setLoading] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [difficulty, setDifficulty] = useState('초급'); // 🎯 난이도 상태 추가
  const panelRef = useRef(null);

  // 현재 마디 변경 시 AI 코칭 요청 함수
  const fetchCoaching = async (measure) => {
    if (!filename) return;
    setLoading(true);
    try {
      const res = await axios.post(`${backendUrl}/api/tutor/coaching`, {
        filename: filename,
        current_measure: measure || 1
      });
      if (res.data && res.data.coaching) {
        const newText = res.data.coaching;
        setCoaching(newText);
        
        // 📝 상위로 히스토리 항목 전송
        if (onSaveHistory) {
          onSaveHistory({
            measure: measure || 1,
            coaching: newText,
            time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
          });
        }
      }
    } catch (err) {
      console.error("AI 코칭 로드 실패:", err);
      setCoaching("AI 코칭 정보를 불러오는 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 마디 또는 난이도가 바뀔 때 자동 조회
  useEffect(() => {
    if (filename && currentMeasure) {
      fetchCoaching(currentMeasure, difficulty);
    }
  }, [filename, currentMeasure, difficulty]);

  return (
    <div 
      ref={panelRef}
      style={{
        backgroundColor: '#1b241e',
        border: '1px solid #2e4a36',
        borderRadius: '10px',
        padding: '12px',
        margin: '12px 0',
        color: '#e0e0e0',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        touchAction: 'manipulation'
      }}
    >
      {/* 헤더 영역 */}
      <div 
        style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center', 
          cursor: 'pointer',
          userSelect: 'none',
          paddingBottom: isCollapsed ? '0' : '8px'
        }}
        onClick={() => setIsCollapsed(!isCollapsed)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span style={{ fontSize: '14px' }}>🤖</span>
          <span style={{ fontWeight: 'bold', fontSize: '13px', color: '#8BC34A' }}>
            AI 레슨 코치
          </span>
          {currentMeasure && (
            <span style={{ 
              fontSize: '10px', 
              backgroundColor: '#2e4a36', 
              color: '#8BC34A', 
              padding: '2px 6px', 
              borderRadius: '10px',
              fontWeight: 'bold' 
            }}>
              {currentMeasure}마디
            </span>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }} onClick={(e) => e.stopPropagation()}>
          {/* 난이도 선택 버튼 3종 */}
          {['초급', '중급', '고급'].map((lev) => (
            <button
              key={lev}
              onClick={() => setDifficulty(lev)}
              style={{
                padding: '2px 6px',
                backgroundColor: difficulty === lev ? '#8BC34A' : '#1e2d23',
                color: difficulty === lev ? '#121914' : '#8BC34A',
                border: '1px solid #8BC34A',
                borderRadius: '4px',
                fontSize: '10px',
                fontWeight: 'bold',
                cursor: 'pointer'
              }}
            >
              {lev}
            </button>
          ))}
          <span style={{ fontSize: '12px', color: '#888', paddingLeft: '4px', cursor: 'pointer' }} onClick={() => setIsCollapsed(!isCollapsed)}>
            {isCollapsed ? '▼' : '▲'}
          </span>
        </div>
      </div>

      {/* 본문 카드 */}
      {!isCollapsed && (
        <div style={{
          fontSize: '12px',
          lineHeight: '1.6',
          backgroundColor: '#121914',
          border: '1px solid #1e2d23',
          padding: '12px',
          borderRadius: '8px',
          whiteSpace: 'pre-wrap',
          minHeight: '65px',
          maxHeight: '200px',
          overflowY: 'auto',
          marginTop: '4px',
          WebkitOverflowScrolling: 'touch'
        }}>
          {loading ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#888' }}>
              <span>⏳ [{difficulty} 모드] Gemini AI가 분석 중입니다...</span>
            </div>
          ) : (
            coaching || '현재 마디에 대한 코칭 정보가 없습니다.'
          )}
        </div>
      )}
    </div>
  );
}