"use client";

import { motion, AnimatePresence } from "framer-motion";
import type { Emotion, MeetingAction } from "@/lib/types";
import {
  ACTION_LABELS,
  EMOTION_BUBBLE_STYLES,
  type EmotionBubbleStyle,
} from "@/lib/meetingUi";

type SpeechBubbleProps = {
  text: string;
  visible: boolean;
  emotion?: Emotion;
  action?: MeetingAction;
  targetRelation?: string;
};

function bubbleMotion(style: EmotionBubbleStyle) {
  if (style.motion === "shake") {
    return {
      initial: { opacity: 0, scale: 0.85, y: 8, x: 0 },
      animate: {
        opacity: 1,
        scale: 1,
        y: 0,
        x: [0, -3, 3, -2, 2, 0],
      },
      exit: { opacity: 0, scale: 0.9, y: 4 },
    };
  }
  if (style.motion === "bounce") {
    return {
      initial: { opacity: 0, scale: 0.85, y: 10 },
      animate: {
        opacity: 1,
        scale: 1,
        y: [8, 0, -4, 0],
      },
      exit: { opacity: 0, scale: 0.9, y: 4 },
    };
  }
  return {
    initial: { opacity: 0, scale: 0.85, y: 8 },
    animate: { opacity: 1, scale: 1, y: 0 },
    exit: { opacity: 0, scale: 0.9, y: 4 },
  };
}

export function SpeechBubble({
  text,
  visible,
  emotion = "neutral",
  action,
  targetRelation,
}: SpeechBubbleProps) {
  const style = EMOTION_BUBBLE_STYLES[emotion];
  const motionProps = bubbleMotion(style);

  return (
    <AnimatePresence>
      {visible && text ? (
        <motion.div
          key={`${text}-${emotion}-${action ?? ""}`}
          {...motionProps}
          transition={{ type: "spring", stiffness: 420, damping: 28 }}
          className="pointer-events-none absolute bottom-full left-1/2 z-20 mb-2 w-[min(260px,calc(100vw-2rem))] max-w-[calc(100vw-2rem)] -translate-x-1/2 sm:mb-3 sm:w-[min(280px,72vw)]"
        >
          <div
            className={`rounded-2xl border px-3 py-2.5 text-sm leading-relaxed shadow-lg sm:px-4 sm:py-3 ${style.panel}`}
          >
            {action ? (
              <span className="mb-1.5 inline-block rounded-full bg-black/5 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-600">
                {ACTION_LABELS[action]}
              </span>
            ) : null}
            {targetRelation ? (
              <p className="mb-1 text-xs font-medium text-slate-600">
                {targetRelation}
              </p>
            ) : null}
            <p className="break-words">{text}</p>
            <div
              className={`absolute -bottom-2 left-1/2 h-4 w-4 -translate-x-1/2 rotate-45 border-b border-r ${style.tail}`}
            />
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
