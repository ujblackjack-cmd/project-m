import React, { useState, useEffect } from 'react';
import axios from 'axios';

export default function AiTutorPanel({ filename, backendUrl, currentMeasure }) {
  const [coaching, setCoaching] = useState('');
  const [loading, setLoading] = useState(false);

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
        setCoaching(res.data.coaching);
      }
    } catch (err) {
      console.error("AI 코칭 로드 실패:", err);
      setCoaching("AI 코칭 정보를 불러오는 중 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  };

  // 마디(currentMeasure)가 바뀔 때마다 AI 코칭 자동 업데이트
  useEffect(() => {
    if (filename && currentMeasure) {
      fetchCoaching(currentMeasure);
    }
  }, [filename, currentMeasure]);

  return (
    <div style={{
      backgroundColor: '#1b241e',
      border: '1px solid #2e4a36',
      borderRadius: '8px',
      padding: '12px',
      margin: '10px 0',
      color: '#e0e0e0'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <span style={{ fontWeight: 'bold', fontSize: '13px', color: '#8BC34A', display: 'flex', alignItems: 'center', gap: '5px' }}>
          🤖 AI 레슨 코치 <span style={{ fontSize: '11px', color: '#aaa', fontWeight: 'normal' }}>({currentMeasure}마디)</span>
        </span>
        <button 
          onClick={() => fetchCoaching(currentMeasure)} 
          disabled={loading}
          style={{ 
            padding: '2px 8px', 
            backgroundColor: '#2e4a36', 
            color: '#8BC34A', 
            border: '1px solid #8BC34A', 
            borderRadius: '4px', 
            fontSize: '10px', 
            cursor: 'pointer' 
          }}
        >
          {loading ? '생성 중...' : '🔄 새로고침'}
        </button>
      </div>

      <div style={{
        fontSize: '12px',
        lineHeight: '1.5',
        backgroundColor: '#121914',
        padding: '10px',
        borderRadius: '6px',
        whiteSpace: 'pre-wrap',
        minHeight: '60px'
      }}>
        {loading ? (
          <span style={{ color: '#888' }}>Gemini AI가 선생님 메모와 타임라인을 분석하고 있습니다...</span>
        ) : (
          coaching || '현재 마디에 대한 코칭 정보가 없습니다.'
        )}
      </div>
    </div>
  );
}