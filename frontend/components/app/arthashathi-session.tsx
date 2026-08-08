'use client';

import React, { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import {
  useAgent,
  useSessionContext,
  useSessionMessages,
  useConnectionState,
} from '@livekit/components-react';
import type { ReceivedMessage } from '@livekit/components-react';
import { AgentControlBar } from '@/components/agents-ui/agent-control-bar';
import { ArthashathiLogo } from './arthashathi-logo';
import { useLanguage } from './language-context';
import { LanguageSelector } from './language-selector';
import { FeatureDetailsModal } from './feature-details-modal';
import type { FeatureCategory } from './feature-data';

// ─────────────────────────────────────────────────────────────────────────────
// Design tokens (all inline so they don't depend on CSS variables)
// ─────────────────────────────────────────────────────────────────────────────
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
  red600:  '#dc2626',
  red50:   '#fff5f5',
  red100:  '#fee2e2',
  saffron: '#FF9933',
  green:   '#138808',
};

// ─────────────────────────────────────────────────────────────────────────────
// Sub-components
// ─────────────────────────────────────────────────────────────────────────────

/** Animated waveform bars — LISTENING state */
function WaveformBars({ size = 56 }: { size?: number }) {
  const heights = [0.45, 0.75, 1, 0.85, 0.6, 1, 0.7, 0.5, 0.9, 0.55];
  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'center', gap: 4, height: size }}>
      {heights.map((h, i) => (
        <div
          key={i}
          style={{
            width: 5,
            borderRadius: 3,
            background: C.teal700,
            height: Math.round(h * size),
            animation: `arthashathi-wave 0.85s ease-in-out ${i * 0.07}s infinite alternate`,
          }}
        />
      ))}
    </div>
  );
}

/** Expanding rings — SPEAKING state */
function SpeakingRings() {
  return (
    <div style={{ position: 'relative', width: 80, height: 80, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      {[0, 0.38, 0.76].map((delay, i) => (
        <div
          key={i}
          style={{
            position: 'absolute',
            inset: 0,
            borderRadius: '50%',
            border: `2.5px solid ${C.gold500}`,
            animation: `arthashathi-ring 1.5s ease-out ${delay}s infinite`,
          }}
        />
      ))}
      <svg viewBox="0 0 24 24" width={28} height={28} fill="none" stroke={C.gold600} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
        <path d="M11 5L6 9H2v6h4l5 4V5z" />
        <path d="M15.54 8.46a5 5 0 0 1 0 7.07" />
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14" />
      </svg>
    </div>
  );
}

/** Simple spinner — CONNECTING state */
function Spinner({ size = 48 }: { size?: number }) {
  return (
    <div
      style={{
        width: size,
        height: size,
        borderRadius: '50%',
        border: `3px solid ${C.teal100}`,
        borderTopColor: C.teal700,
        animation: 'arthashathi-spin 0.75s linear infinite',
      }}
    />
  );
}

/** Trust badge row */
function TrustBadge({ icon, label }: { icon: string; label: string }) {
  return (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 6,
      padding: '6px 14px', borderRadius: 999,
      background: C.teal50, border: `1px solid ${C.teal100}`,
      fontSize: 12, fontWeight: 600, color: C.teal800,
    }}>
      <span style={{ fontSize: 14 }}>{icon}</span>
      {label}
    </div>
  );
}

/** Feature card */
function FeatureCard({ icon, title, desc }: { icon: string; title: string; desc: string }) {
  return (
    <div style={{
      background: C.white, borderRadius: 16, padding: '20px 18px',
      border: `1px solid ${C.teal100}`, display: 'flex', flexDirection: 'column', gap: 8,
      boxShadow: '0 2px 12px rgba(13,110,115,0.06)',
    }}>
      <span style={{ fontSize: 26 }}>{icon}</span>
      <p style={{ margin: 0, fontWeight: 700, fontSize: 14, color: C.teal900 }}>{title}</p>
      <p style={{ margin: 0, fontSize: 12, color: C.slate500, lineHeight: 1.5 }}>{desc}</p>
    </div>
  );
}

/** Single transcript message bubble */
function TranscriptBubble({ msg, youLabel }: { msg: ReceivedMessage; youLabel: string }) {
  const isUser = msg.from?.isLocal === true;
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22 }}
      style={{
        display: 'flex', flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        marginBottom: 12,
      }}
    >
      <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: isUser ? C.slate500 : C.teal700, marginBottom: 4 }}>
        {isUser ? youLabel : 'Arthashathi'}
      </span>
      <div style={{
        maxWidth: '82%',
        padding: '10px 16px',
        borderRadius: isUser ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
        background: isUser ? C.slate200 : C.teal50,
        border: isUser ? 'none' : `1px solid ${C.teal100}`,
        color: isUser ? C.slate700 : C.teal900,
        fontSize: 14,
        lineHeight: 1.55,
      }}>
        {msg.message}
      </div>
    </motion.div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main session view
// ─────────────────────────────────────────────────────────────────────────────
export function ArthashathiSessionView() {
  const session = useSessionContext();
  const connectionState = useConnectionState();
  const { messages } = useSessionMessages(session);
  const { state: agentState } = useAgent();
  const transcriptRef = useRef<HTMLDivElement>(null);
  const { t } = useLanguage();
  const [activeFeature, setActiveFeature] = useState<{ category: FeatureCategory; title: string } | null>(null);

  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [messages, agentState]);

  const isConnecting = connectionState === 'connecting';
  const isListening  = agentState === 'listening';
  const isThinking   = agentState === 'thinking';
  const isSpeaking   = agentState === 'speaking' || isThinking;

  // State-specific copy
  const stateLabel = isConnecting
    ? t('statusConnecting')
    : isSpeaking
      ? t('statusSpeaking')
      : isListening
        ? t('statusListening')
        : t('statusConnected');

  const stateLabelColor = isSpeaking ? C.gold600 : C.teal700;

  return (
    <div style={{
      minHeight: '100svh', display: 'flex', flexDirection: 'column',
      background: `linear-gradient(160deg, ${C.teal50} 0%, #f9fafb 55%, ${C.gold50} 100%)`,
      fontFamily: 'inherit',
    }}>
      {/* ── Keyframe styles ── */}
      <style>{`
        @keyframes arthashathi-spin { to { transform: rotate(360deg); } }
        @keyframes arthashathi-wave {
          from { transform: scaleY(0.2); opacity: 0.4; }
          to   { transform: scaleY(1);   opacity: 1;   }
        }
        @keyframes arthashathi-ring {
          0%   { transform: scale(1);   opacity: 0.7; }
          100% { transform: scale(2.4); opacity: 0;   }
        }
        @keyframes arthashathi-dot {
          0%, 80%, 100% { transform: translateY(0); }
          40%           { transform: translateY(-6px); }
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
          {/* Tricolor accent line */}
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
          {/* Live status pill */}
          <div style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '5px 14px', borderRadius: 999,
            background: isSpeaking ? C.gold50 : C.teal50,
            border: `1px solid ${isSpeaking ? '#fde68a' : C.teal100}`,
            fontSize: 12, fontWeight: 600, color: stateLabelColor,
            transition: 'all 0.25s',
          }}>
            <div style={{
              width: 7, height: 7, borderRadius: '50%',
              background: isSpeaking ? C.gold500 : isConnecting ? C.teal700 : C.green,
              animation: isConnecting || isSpeaking || isListening ? 'arthashathi-dot 1.2s ease-in-out infinite' : 'none',
            }} />
            <span className="hidden sm:inline">{stateLabel}</span>
          </div>
          <LanguageSelector />
        </div>
      </header>

      {/* ── SCROLLABLE BODY ── */}
      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>

        {/* ── HERO ── */}
        <section style={{
          maxWidth: 900, width: '100%', margin: '0 auto',
          padding: '40px 24px 32px',
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
          gap: 40, alignItems: 'center',
        }}>
          {/* Left: description */}
          <div>
            <h1 style={{ margin: '0 0 12px', fontSize: 26, fontWeight: 800, color: C.teal900, lineHeight: 1.25, whiteSpace: 'pre-line' }}>
              {t('heroTitle')}
            </h1>
            <p style={{ margin: '0 0 20px', fontSize: 14, color: C.slate500, lineHeight: 1.7 }}>
              {t('heroDesc')}
            </p>
            {/* Tricolor divider */}
            <div style={{ display: 'flex', height: 3, width: 120, borderRadius: 3, overflow: 'hidden', marginBottom: 20 }}>
              <div style={{ flex: 1, background: C.saffron }} />
              <div style={{ flex: 1, background: '#e5e7eb' }} />
              <div style={{ flex: 1, background: C.green }} />
            </div>
            <p style={{ margin: 0, fontSize: 12, color: C.teal700, fontWeight: 600 }}>
              🛡️&nbsp; {t('footer2')} <strong>1930</strong> &nbsp;|&nbsp; {t('footer3')}
            </p>
          </div>

          {/* Right: State indicator circle */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16 }}>
            <AnimatePresence mode="wait">
              <motion.div
                key={isConnecting ? 'conn' : isSpeaking ? 'speak' : isListening ? 'listen' : 'idle'}
                initial={{ opacity: 0, scale: 0.88 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.88 }}
                transition={{ duration: 0.25 }}
                style={{
                  width: 140, height: 140,
                  borderRadius: '50%',
                  background: isSpeaking
                    ? `radial-gradient(circle at 38% 38%, ${C.gold100}, ${C.gold50})`
                    : `radial-gradient(circle at 38% 38%, ${C.teal100}, ${C.teal50})`,
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: isSpeaking
                    ? `0 0 0 12px ${C.gold50}, 0 8px 40px rgba(217,119,6,0.18)`
                    : `0 0 0 12px ${C.teal50}, 0 8px 40px rgba(13,110,115,0.15)`,
                  transition: 'background 0.3s, box-shadow 0.3s',
                }}
              >
                {isConnecting && <Spinner size={52} />}
                {!isConnecting && isSpeaking && <SpeakingRings />}
                {!isConnecting && isListening && <WaveformBars size={60} />}
                {!isConnecting && !isSpeaking && !isListening && (
                  <ArthashathiLogo size={60} />
                )}
              </motion.div>
            </AnimatePresence>
            <p style={{ margin: 0, fontSize: 14, fontWeight: 700, color: stateLabelColor, textAlign: 'center', transition: 'color 0.25s' }}>
              {stateLabel}
            </p>
          </div>
        </section>

        {/* ── TRANSCRIPT ── */}
        {(messages.length > 0 || isThinking) && (
          <section style={{ maxWidth: 900, width: '100%', margin: '0 auto', padding: '0 24px 16px' }}>
            <div style={{ background: C.white, borderRadius: 20, border: `1px solid ${C.teal100}`, overflow: 'hidden', boxShadow: '0 2px 16px rgba(13,110,115,0.07)' }}>
              <div style={{ padding: '12px 20px', borderBottom: `1px solid ${C.teal50}`, display: 'flex', alignItems: 'center', gap: 8 }}>
                <div style={{ width: 8, height: 8, borderRadius: '50%', background: C.green }} />
                <span style={{ fontSize: 11, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: C.teal700 }}>{t('liveTranscript')}</span>
              </div>
              <div
                ref={transcriptRef}
                style={{ maxHeight: 320, overflowY: 'auto', padding: '16px 20px' }}
              >
                {messages.length === 0 && !isThinking && (
                  <div style={{ padding: '20px', textAlign: 'center', color: C.slate500, fontSize: 13 }}>
                    <p style={{ marginBottom: 4 }}>{t('transcriptEmpty1')}</p>
                    <p>{t('transcriptEmpty2')}</p>
                  </div>
                )}
                {messages.map((msg, i) => <TranscriptBubble key={msg.id ?? i} msg={msg} youLabel={t('you')} />)}
                {isThinking && (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', marginBottom: 8 }}>
                    <span style={{ fontSize: 10, fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase', color: C.teal700, marginBottom: 4 }}>Arthashathi</span>
                    <div style={{ display: 'flex', gap: 5, padding: '10px 16px', background: C.teal50, borderRadius: '18px 18px 18px 4px', border: `1px solid ${C.teal100}` }}>
                      {[0, 0.18, 0.36].map((d, i) => (
                        <div key={i} style={{ width: 7, height: 7, borderRadius: '50%', background: C.teal700, animation: `arthashathi-dot 1.1s ease-in-out ${d}s infinite` }} />
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </section>
        )}

        {/* ── FEATURE CARDS ── */}
        <section style={{ maxWidth: 900, width: '100%', margin: '0 auto', padding: '8px 24px 32px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 14 }}>
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
                  display: 'flex', flexDirection: 'column', gap: 8
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
                <p style={{ margin: 0, fontWeight: 700, fontSize: 14, color: C.teal900 }}>{title}</p>
                <p style={{ margin: 0, fontSize: 12, color: C.slate500, lineHeight: 1.5 }}>{desc}</p>
              </button>
            ))}
          </div>
        </section>
      </div>

      {/* ── FIXED FOOTER CONTROLS ── */}
      <footer style={{
        background: 'rgba(255,255,255,0.97)',
        borderTop: `1px solid ${C.teal100}`,
        padding: '12px 24px',
        flexShrink: 0,
        backdropFilter: 'blur(8px)',
        display: 'flex', justifyContent: 'center',
      }}>
        <div style={{ width: '100%', maxWidth: 420 }}>
          <AgentControlBar
            variant="outline"
            isConnected={session.isConnected}
            onDisconnect={session.end}
            controls={{ leave: true, microphone: true, chat: false, camera: false, screenShare: false }}
            className="rounded-2xl border-teal-100 bg-white shadow-md"
          />
        </div>
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
}
