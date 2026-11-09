import React, { useState } from 'react';

export default function LessonHistoryModal({ isOpen, onClose, historyList, onSelectMeasure }) {
  const [filterMeasure, setFilterMeasure] = useState('all');

  if (!isOpen) return null;

  // 마디 필터링
  const filteredList = filterMeasure === 'all' 
    ? historyList 
    : historyList.filter(item => String(item.measure) === String(filterMeasure));

  // 고유 마디 목록 추출
  const uniqueMeasures = Array.from(new Set(historyList.map(item => item.measure))).sort((a, b) => a - b);

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      width: '100vw',
      height: '100vh',
      backgroundColor: 'rgba(0, 0, 0, 0.75)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      zIndex: 1000,
      backdropFilter: 'blur(4px)'
    }}>
      <div style={{
        backgroundColor: '#181818',
        border: '1px solid #333',
        borderRadius: '12px',
        width: '90%',
        maxWidth: '550px',
        maxHeight: '80vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 10px 25px rgba(0, 0, 0, 0.5)',
        color: '#e0e0e0'
      }}>
        {/* 모달 헤더 */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid #2a2a2a',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h3 style={{ margin: 0, fontSize: '16px', color: '#8BC34A', display: 'flex', alignItems: 'center', gap: '8px' }}>
            📝 레슨 피드백 히스토리 (오답 노트)
          </h3>
          <button 
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: '#aaa',
              fontSize: '18px',
              cursor: 'pointer'
            }}
          >
            ✕
          </button>
        </div>

        {/* 필터 바 */}
        <div style={{ padding: '12px 20px', backgroundColor: '#121212', borderBottom: '1px solid #2a2a2a', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '12px', color: '#888' }}>마디 필터:</span>
          <select 
            value={filterMeasure} 
            onChange={(e) => setFilterMeasure(e.target.value)}
            style={{
              backgroundColor: '#222',
              color: '#fff',
              border: '1px solid #444',
              borderRadius: '4px',
              padding: '4px 8px',
              fontSize: '12px'
            }}
          >
            <option value="all">전체 마디 보기 ({historyList.length})</option>
            {uniqueMeasures.map(m => (
              <option key={m} value={m}>{m}마디 피드백</option>
            ))}
          </select>
        </div>

        {/* 히스토리 리스트 본문 */}
        <div style={{ padding: '16px', overflowY: 'auto', flex: 1 }}>
          {filteredList.length === 0 ? (
            <div style={{ textAlign: 'center', color: '#666', padding: '30px 0', fontSize: '13px' }}>
              저장된 연습 피드백 기록이 없습니다.
            </div>
          ) : (
            filteredList.map((item, index) => (
              <div 
                key={index} 
                style={{
                  backgroundColor: '#222',
                  border: '1px solid #333',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '10px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span 
                    onClick={() => {
                      if (onSelectMeasure) onSelectMeasure(item.measure);
                      onClose();
                    }}
                    style={{ 
                      fontSize: '12px', 
                      fontWeight: 'bold', 
                      color: '#8BC34A', 
                      cursor: 'pointer',
                      textDecoration: 'underline'
                    }}
                  >
                    🎯 {item.measure}마디로 이동
                  </span>
                  <span style={{ fontSize: '10px', color: '#777' }}>{item.time}</span>
                </div>
                <div style={{ fontSize: '12px', lineHeight: '1.5', color: '#ccc', whiteSpace: 'pre-wrap' }}>
                  {item.coaching}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}