'use client';

import React, { useState } from 'react';
import { ArthashathiLogo } from './arthashathi-logo';
import { useLanguage } from './language-context';
import { LanguageSelector } from './language-selector';
import { FeatureDetailsModal } from './feature-details-modal';
import type { FeatureCategory } from './feature-data';

// Design tokens (mirrored from session view)
const C = {
  teal900: '#0a3f42',
  teal800: '#0d5459',
  teal700: '#0d6e73',
  teal200: '#99d6d9',
  teal100: '#d1eff0',
  teal50:  '#e8f7f8',
  gold600: '#d97706',
  gold500: '#f59e0b',
  gold100: '#fef3c7',
  gold50:  '#fffbeb',
  bg:      '#f4f8f8',
  white:   '#ffffff',
  slate700:'#374151',
  slate500:'#6b7280',
  slate200:'#e5e7eb',
  red700:  '#b91c1c',
  red600:  '#dc2626',
  red50:   '#fff5f5',
  red100:  '#fee2e2',
  red200:  '#fecaca',
  saffron: '#FF9933',
  green:   '#138808',
};

interface ArthashathiWelcomeProps {
  startButtonText: string;
  onStartCall: () => Promise<void> | void;
}

export const ArthashathiWelcomeView = ({
  startButtonText,
  onStartCall,
  ref,
}: React.ComponentProps<'div'> & ArthashathiWelcomeProps) => {
  const { t } = useLanguage();
  const [phase, setPhase] = useState<'ready' | 'connecting' | 'error'>('ready');
  const [activeFeature, setActiveFeature] = useState<{ category: FeatureCategory; title: string } | null>(null);

  const handleStart = async () => {
    setPhase('connecting');
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      await onStartCall();
      // onStartCall triggers the LiveKit connection; once isConnected flips
      // the ViewController will unmount this component entirely.
    } catch (err: any) {
      console.error('Microphone / connection error:', err);
      if (err.name === 'NotAllowedError' || err.name === 'NotFoundError' || err.name === 'OverconstrainedError') {
        setPhase('error');
      } else {
        // Network or auth error — reset to ready so user can retry
        setPhase('ready');
      }
    }
  };

  return (
    <div
      ref={ref}
      style={{
        minHeight: '100svh',
        display: 'flex',
        flexDirection: 'column',
        background: `linear-gradient(160deg, ${C.teal50} 0%, #f9fafb 55%, ${C.gold50} 100%)`,
        fontFamily: 'inherit',
      }}
    >
      <style>{`
        @keyframes arthashathi-spin { to { transform: rotate(360deg); } }
        @keyframes arthashathi-pulse-ring {
          0%   { transform: scale(1);   opacity: 0.7; }
          100% { transform: scale(1.7); opacity: 0;   }
        }
        @keyframes arthashathi-breathe {
          0%, 100% { box-shadow: 0 0 0 0 rgba(13,110,115,0.18), 0 8px 40px rgba(13,110,115,0.15); }
          50%       { box-shadow: 0 0 0 18px rgba(13,110,115,0.06), 0 8px 40px rgba(13,110,115,0.15); }
        }
      `}</style>

      {/* ── HEADER ── */}
      <header style={{
        background: C.white,
        borderBottom: `1px solid ${C.teal100}`,
        padding: '0 24px',
        height: 60,
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        flexShrink: 0,
        boxShadow: '0 1px 6px rgba(13,110,115,0.08)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          {/* Tricolor accent */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <div style={{ width: 4, height: 8, borderRadius: 2, background: C.saffron }} />
            <div style={{ width: 4, height: 8, borderRadius: 2, background: C.white, border: `1px solid ${C.slate200}` }} />
            <div style={{ width: 4, height: 8, borderRadius: 2, background: C.green }} />
          </div>
          <ArthashathiLogo size={26} />
          <div>
            <p style={{ margin: 0, fontWeight: 800, fontSize: 15, color: C.teal900, lineHeight: 1.1 }}>{t('appName')}</p>
            <p style={{ margin: 0, fontSize: 10, color: C.teal700, lineHeight: 1.1 }}>{t('tagline')}</p>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <div style={{
            padding: '5px 14px', borderRadius: 999,
            background: C.teal50, border: `1px solid ${C.teal100}`,
            fontSize: 11, fontWeight: 700, color: C.teal800,
            letterSpacing: '0.04em', display: 'flex', alignItems: 'center', gap: 4
          }}>
            <span className="hidden sm:inline">🔒</span> {t('secureConnection')}
          </div>
          <LanguageSelector />
        </div>
      </header>

      {/* ── MAIN ── */}
      <main style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>

        {/* ── MIC ERROR CARD ── */}
        {phase === 'error' && (
          <div style={{
            maxWidth: 500, width: '100%', margin: '40px 24px',
            background: C.white, borderRadius: 24,
            border: `1.5px solid ${C.red200}`,
            boxShadow: '0 4px 24px rgba(220,38,38,0.08)',
            overflow: 'hidden',
          }}>
            <div style={{ background: C.red100, padding: '20px 24px', display: 'flex', alignItems: 'flex-start', gap: 14 }}>
              <div style={{
                width: 44, height: 44, borderRadius: '50%', flexShrink: 0,
                background: C.red50, border: `2px solid ${C.red200}`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 22,
              }}>🎙️</div>
              <div>
                <p style={{ margin: '0 0 4px', fontWeight: 800, fontSize: 16, color: C.red700 }}>{t('micRequired')}</p>
                <p style={{ margin: 0, fontSize: 13, color: '#b91c1c', lineHeight: 1.55 }}>
                  {t('micRequiredDesc')}
                </p>
              </div>
            </div>
            <div style={{ padding: '20px 24px' }}>
              <p style={{ margin: '0 0 12px', fontWeight: 700, fontSize: 13, color: C.slate700 }}>{t('enableMic')}</p>
              <ol style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: C.slate700, lineHeight: 1.8 }}>
                <li>Look for a <strong>🔒 lock</strong> or <strong>📷 camera</strong> icon in your browser address bar.</li>
                <li>Click it and find <strong>Microphone</strong> in the list.</li>
                <li>Change the setting to <strong>"Allow"</strong>.</li>
                <li>Come back to this page and tap <strong>"Try Again"</strong> below.</li>
              </ol>
              <div style={{ marginTop: 20, display: 'flex', gap: 10 }}>
                <button
                  onClick={() => window.location.reload()}
                  style={{
                    flex: 1, padding: '13px 0', borderRadius: 12, border: 'none',
                    background: C.red600, color: C.white,
                    fontWeight: 700, fontSize: 14, cursor: 'pointer',
                    minHeight: 48,
                  }}
                >
                  🔄 {t('reloadTryAgain')}
                </button>
                <button
                  onClick={() => setPhase('ready')}
                  style={{
                    flex: 1, padding: '13px 0', borderRadius: 12,
                    border: `1.5px solid ${C.red200}`,
                    background: C.white, color: C.red700,
                    fontWeight: 600, fontSize: 14, cursor: 'pointer',
                    minHeight: 48,
                  }}
                >
                  ← {t('goBack')}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── HERO (READY / CONNECTING) ── */}
        {phase !== 'error' && (
          <div style={{
            maxWidth: 900, width: '100%', margin: '0 auto', padding: '44px 24px 32px',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: 48, alignItems: 'center',
          }}>
            {/* Left: copy */}
            <div>
              <h1 style={{ margin: '0 0 14px', fontSize: 28, fontWeight: 800, color: C.teal900, lineHeight: 1.22, whiteSpace: 'pre-line' }}>
                {t('heroTitle')}
              </h1>
              <p style={{ margin: '0 0 22px', fontSize: 14, color: C.slate500, lineHeight: 1.75 }}>
                {t('heroDesc')}
              </p>
              {/* Tricolor divider */}
              <div style={{ display: 'flex', height: 3, width: 120, borderRadius: 3, overflow: 'hidden', marginBottom: 22 }}>
                <div style={{ flex: 1, background: C.saffron }} />
                <div style={{ flex: 1, background: '#e5e7eb' }} />
                <div style={{ flex: 1, background: C.green }} />
              </div>
              {/* Trust row */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {[
                  { icon: '🔒', label: t('trust1') },
                  { icon: '📋', label: t('trust2') },
                  { icon: '📞', label: t('trust3') },
                ].map(({ icon, label }) => (
                  <div key={label} style={{
                    display: 'flex', alignItems: 'center', gap: 5,
                    padding: '5px 12px', borderRadius: 999,
                    background: C.teal50, border: `1px solid ${C.teal100}`,
                    fontSize: 12, fontWeight: 600, color: C.teal800,
                  }}>
                    <span>{icon}</span>{label}
                  </div>
                ))}
              </div>
            </div>

            {/* Right: call button */}
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 18 }}>
              {/* Outer ring container */}
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {/* Breathing/pulsing halo */}
                {phase === 'ready' && (
                  <div style={{
                    position: 'absolute', inset: -16,
                    borderRadius: '50%',
                    animation: 'arthashathi-pulse-ring 2s ease-out infinite',
                    background: 'transparent',
                    border: `2px solid ${C.teal200}`,
                    pointerEvents: 'none',
                  }} />
                )}
                <button
                  onClick={handleStart}
                  disabled={phase === 'connecting'}
                  style={{
                    width: 150, height: 150,
                    borderRadius: '50%',
                    border: 'none',
                    cursor: phase === 'connecting' ? 'wait' : 'pointer',
                    display: 'flex', flexDirection: 'column',
                    alignItems: 'center', justifyContent: 'center', gap: 8,
                    background: phase === 'connecting'
                      ? `radial-gradient(circle at 38% 38%, ${C.teal100}, ${C.teal50})`
                      : `radial-gradient(circle at 38% 38%, ${C.gold100}, ${C.gold50})`,
                    boxShadow: phase === 'connecting'
                      ? `0 0 0 14px ${C.teal50}, 0 12px 48px rgba(13,110,115,0.18)`
                      : `0 0 0 14px rgba(245,158,11,0.12), 0 12px 48px rgba(217,119,6,0.22)`,
                    transition: 'all 0.3s',
                    animation: phase === 'ready' ? 'arthashathi-breathe 2.5s ease-in-out infinite' : 'none',
                  }}
                >
                  {phase === 'connecting' ? (
                    <>
                      <div style={{
                        width: 42, height: 42, borderRadius: '50%',
                        border: `3px solid ${C.teal100}`,
                        borderTopColor: C.teal700,
                        animation: 'arthashathi-spin 0.75s linear infinite',
                      }} />
                    </>
                  ) : (
                    <>
                      {/* Mic SVG */}
                      <svg viewBox="0 0 24 24" width={38} height={38} fill="none" stroke={C.gold600} strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
                        <rect x="9" y="2" width="6" height="11" rx="3" />
                        <path d="M5 10a7 7 0 0 0 14 0" />
                        <line x1="12" y1="19" x2="12" y2="22" />
                        <line x1="8" y1="22" x2="16" y2="22" />
                      </svg>
                    </>
                  )}
                </button>
              </div>

              <div style={{ textAlign: 'center' }}>
                <p style={{
                  margin: '0 0 4px',
                  fontWeight: 800, fontSize: 16,
                  color: phase === 'connecting' ? C.teal700 : C.gold600,
                  transition: 'color 0.3s',
                }}>
                  {phase === 'connecting' ? t('buttonConnecting') : t('buttonReady')}
                </p>
                {phase === 'ready' && (
                  <p style={{ margin: 0, fontSize: 12, color: C.slate500 }}>
                    {t('tapToStart')}
                  </p>
                )}
                {phase === 'connecting' && (
                  <p style={{ margin: 0, fontSize: 12, color: C.teal700 }}>
                    {t('connectingTo')}
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── FEATURE CARDS ── */}
        {phase !== 'error' && (
          <section style={{ maxWidth: 900, width: '100%', margin: '0 auto', padding: '0 24px 44px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: 14 }}>
              {[
                { category: 'schemes', icon: '🏛️', title: t('card1Title'), desc: t('card1Desc') },
                { category: 'fraud', icon: '🛡️', title: t('card2Title'), desc: t('card2Desc') },
                { category: 'banking', icon: '🏦', title: t('card3Title'), desc: t('card3Desc') },
                { category: 'helpline', icon: '📞', title: t('card4Title'), desc: t('card4Desc') },
              ].map(({ category, icon, title, desc }) => (
                <button 
                  key={title} 
                  onClick={() => setActiveFeature({ category: category as FeatureCategory, title })}
                  style={{
                    background: C.white, borderRadius: 16, padding: '20px 18px',
                    border: `1px solid ${C.teal100}`, textAlign: 'left',
                    boxShadow: '0 2px 12px rgba(13,110,115,0.06)',
                    cursor: 'pointer', transition: 'all 0.2s',
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 6px 16px rgba(13,110,115,0.1)';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.transform = 'none';
                    e.currentTarget.style.boxShadow = '0 2px 12px rgba(13,110,115,0.06)';
                  }}
                >
                  <span style={{ fontSize: 26 }}>{icon}</span>
                  <p style={{ margin: '10px 0 6px', fontWeight: 700, fontSize: 14, color: C.teal900 }}>{title}</p>
                  <p style={{ margin: 0, fontSize: 12, color: C.slate500, lineHeight: 1.55 }}>{desc}</p>
                </button>
              ))}
            </div>
          </section>
        )}
      </main>

      {/* ── FOOTER ── */}
      <footer style={{
        background: C.white,
        borderTop: `1px solid ${C.teal100}`,
        padding: '10px 24px',
        display: 'flex', justifyContent: 'center', gap: 20, flexWrap: 'wrap',
        fontSize: 11, color: C.slate500,
        flexShrink: 0,
      }}>
        <span>{t('footer1')}</span>
        <span style={{ color: C.teal100 }}>|</span>
        <span>{t('footer2')} <strong style={{ color: C.teal700 }}>1930</strong></span>
        <span style={{ color: C.teal100 }}>|</span>
        <span>{t('footer3')}</span>
      </footer>

      {/* Feature Details Modal */}
      {activeFeature && (
        <FeatureDetailsModal 
          category={activeFeature.category}
          title={activeFeature.title}
          onClose={() => setActiveFeature(null)}
        />
      )}
    </div>
  );
};
