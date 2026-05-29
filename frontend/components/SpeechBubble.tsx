"use client";

import { motion, AnimatePresence } from "framer-motion";
import type { Emotion } from "@/lib/types";
import {
  EMOTION_BUBBLE_STYLES,
  type EmotionBubbleStyle,
} from "@/lib/meetingUi";

export type BubblePlacement = "top" | "bottom";

type SpeechBubbleProps = {
  text: string;
  visible: boolean;
  placement?: BubblePlacement;
  emotion?: Emotion;
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
}: SpeechBubbleProps) {
  const style = EMOTION_BUBBLE_STYLES[emotion];
  const { transition, ...motionProps } = bubbleMotion(style);
  const tailPointsUp = placement === "bottom";

  return (
    <AnimatePresence>
      {visible && text ? (
        <motion.div
          key={`${text}-${emotion}-${placement}`}
          {...motionProps}
          transition={transition}
          className={`pointer-events-none absolute left-1/2 z-20 -translate-x-1/2 ${PLACEMENT_CLASS[placement]}`}
        >
          <div
            className={`relative whitespace-nowrap rounded-full border px-3.5 py-1.5 text-xs font-bold shadow-lg ring-2 ring-white/80 sm:px-4 sm:py-2 sm:text-sm ${style.panel}`}
          >
            {tailPointsUp ? (
              <div
                className={`absolute -top-1.5 left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 border-l border-t ${style.tail}`}
              />
            ) : null}
            <span>{text}</span>
            {!tailPointsUp ? (
              <div
                className={`absolute -bottom-1.5 left-1/2 h-3 w-3 -translate-x-1/2 rotate-45 border-b border-r ${style.tail}`}
              />
            ) : null}
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
