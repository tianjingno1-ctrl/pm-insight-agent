"use client";

import { motion, AnimatePresence } from "framer-motion";
import type { Emotion, MeetingAction } from "@/lib/types";
import {
  ACTION_LABELS,
  EMOTION_BUBBLE_STYLES,
  type EmotionBubbleStyle,
} from "@/lib/meetingUi";

export type BubblePlacement = "top" | "bottom";

type SpeechBubbleProps = {
  text: string;
  visible: boolean;
  placement?: BubblePlacement;
  emotion?: Emotion;
  action?: MeetingAction;
  targetRelation?: string;
};

const PLACEMENT_CLASS: Record<BubblePlacement, string> = {
  top: "bottom-full mb-2 sm:mb-3",
  bottom: "top-full mt-2 sm:mt-3",
};

/** Multi-keyframe paths must use tween; spring/inertia only support ≤2 keyframes. */
const KEYFRAME_TWEEN = {
  type: "tween" as const,
  duration: 0.35,
  ease: "easeInOut" as const,
};

const ENTER_SPRING = {
  type: "spring" as const,
  stiffness: 420,
  damping: 28,
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
      transition: KEYFRAME_TWEEN,
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
      transition: KEYFRAME_TWEEN,
    };
  }
  return {
    initial: { opacity: 0, scale: 0.85, y: 8 },
    animate: { opacity: 1, scale: 1, y: 0 },
    exit: { opacity: 0, scale: 0.9, y: 4 },
    transition: ENTER_SPRING,
  };
}

export function SpeechBubble({
  text,
  visible,
  placement = "top",
  emotion = "neutral",
  action,
  targetRelation,
}: SpeechBubbleProps) {
  const style = EMOTION_BUBBLE_STYLES[emotion];
  const { transition, ...motionProps } = bubbleMotion(style);
  const tailPointsUp = placement === "bottom";

  return (
    <AnimatePresence>
      {visible && text ? (
        <motion.div
          key={`${text}-${emotion}-${action ?? ""}-${placement}`}
          {...motionProps}
          transition={transition}
          className={`pointer-events-none absolute left-1/2 z-20 w-[min(260px,calc(100vw-2rem))] max-w-[calc(100vw-2rem)] -translate-x-1/2 sm:w-[min(280px,72vw)] ${PLACEMENT_CLASS[placement]}`}
        >
          <div
            className={`relative rounded-2xl border px-3 py-2.5 text-sm leading-relaxed shadow-lg sm:px-4 sm:py-3 ${style.panel}`}
          >
            {tailPointsUp ? (
              <div
                className={`absolute -top-2 left-1/2 h-4 w-4 -translate-x-1/2 rotate-45 border-l border-t ${style.tail}`}
              />
            ) : null}
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
            {!tailPointsUp ? (
              <div
                className={`absolute -bottom-2 left-1/2 h-4 w-4 -translate-x-1/2 rotate-45 border-b border-r ${style.tail}`}
              />
            ) : null}
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
