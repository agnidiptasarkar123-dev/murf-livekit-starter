'use client';

import { AnimatePresence, motion } from 'motion/react';
import { useSessionContext } from '@livekit/components-react';
import type { AppConfig } from '@/app-config';
import { ArthashathiSessionView } from './arthashathi-session';
import { ArthashathiWelcomeView } from './arthashathi-welcome';

const MotionWelcomeView = motion.create(ArthashathiWelcomeView);
const MotionSessionView = motion.create(ArthashathiSessionView);

const VIEW_MOTION_PROPS = {
  variants: {
    visible: { opacity: 1 },
    hidden:  { opacity: 0 },
  },
  initial: 'hidden',
  animate: 'visible',
  exit: 'hidden',
  transition: { duration: 0.4, ease: 'easeInOut' },
};

interface ViewControllerProps {
  appConfig: AppConfig;
}

export function ViewController({ appConfig }: ViewControllerProps) {
  const { isConnected, start } = useSessionContext();

  return (
    // Fills the full <main> that the app renders into — no extra wrappers
    <div className="h-svh w-full">
      <AnimatePresence mode="wait">
        {!isConnected && (
          <MotionWelcomeView
            key="welcome"
            {...VIEW_MOTION_PROPS}
            startButtonText={appConfig.startButtonText}
            onStartCall={start}
          />
        )}
        {isConnected && (
          <MotionSessionView
            key="session-view"
            {...VIEW_MOTION_PROPS}
          />
        )}
      </AnimatePresence>
    </div>
  );
}
