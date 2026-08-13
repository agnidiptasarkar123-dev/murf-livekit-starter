'use client';

import React, { useEffect, useRef, useState } from 'react';
import { Globe } from 'lucide-react';
import { useLanguage } from './language-context';
import { type LanguageCode, languages } from './translations';

export function LanguageSelector() {
  const { language, setLanguage } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const currentLang = languages.find((l) => l.code === language) || languages[0];

  return (
    <div className="relative" ref={dropdownRef} style={{ zIndex: 50 }}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          padding: '6px 12px',
          borderRadius: 999,
          background: '#f4f8f8',
          border: '1px solid #d1eff0',
          cursor: 'pointer',
          transition: 'all 0.2s',
          fontSize: 13,
          fontWeight: 600,
          color: '#0a3f42',
        }}
        onMouseOver={(e) => (e.currentTarget.style.background = '#e8f7f8')}
        onMouseOut={(e) => (e.currentTarget.style.background = '#f4f8f8')}
      >
        <Globe size={16} color="#0d6e73" />
        <span className="hidden sm:inline">{currentLang.nativeName}</span>
        <span className="sm:hidden">{currentLang.code.toUpperCase()}</span>
      </button>

      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: '100%',
            right: 0,
            marginTop: 8,
            background: '#ffffff',
            border: '1px solid #d1eff0',
            borderRadius: 12,
            boxShadow: '0 10px 25px rgba(13,110,115,0.1)',
            minWidth: 160,
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            maxHeight: 300,
            overflowY: 'auto',
          }}
        >
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                setLanguage(lang.code as LanguageCode);
                setIsOpen(false);
              }}
              style={{
                width: '100%',
                textAlign: 'left',
                padding: '10px 16px',
                background: language === lang.code ? '#e8f7f8' : 'transparent',
                border: 'none',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: 14,
                color: language === lang.code ? '#0d6e73' : '#374151',
                fontWeight: language === lang.code ? 700 : 500,
              }}
              onMouseOver={(e) => {
                if (language !== lang.code) e.currentTarget.style.background = '#f9fafb';
              }}
              onMouseOut={(e) => {
                if (language !== lang.code) e.currentTarget.style.background = 'transparent';
              }}
            >
              <span>{lang.nativeName}</span>
              <span style={{ fontSize: 11, color: '#9ca3af' }}>{lang.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
