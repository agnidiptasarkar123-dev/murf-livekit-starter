'use client';

import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { type LanguageCode, translations } from './translations';

interface LanguageContextType {
  language: LanguageCode;
  setLanguage: (lang: LanguageCode) => void;
  t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<LanguageCode>('en');

  // Load language preference on mount safely
  useEffect(() => {
    try {
      const savedLang = localStorage.getItem('arthashathi_lang') as LanguageCode;
      if (savedLang && translations[savedLang]) {
        setLanguageState(savedLang);
      }
    } catch (e) {
      console.error('Failed to read language preference', e);
    }
  }, []);

  // Update language and persist
  const setLanguage = useCallback((lang: LanguageCode) => {
    setLanguageState(lang);
    try {
      localStorage.setItem('arthashathi_lang', lang);
    } catch (e) {
      console.error('Failed to save language preference', e);
    }
  }, []);

  // Translation function
  const t = useCallback(
    (key: string): string => {
      const dict = translations[language] || translations.en;
      return dict[key] || translations.en[key] || key;
    },
    [language]
  );

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
