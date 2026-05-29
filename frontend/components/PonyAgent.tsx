"use client";

import { motion } from "framer-motion";
import type { AgentConfig, Emotion } from "@/lib/types";
import { SpeechBubble, type BubblePlacement } from "./SpeechBubble";

const emotionRing: Record<Emotion, string> = {
  neutral: "ring-white/90",
  happy: "ring-emerald-300",
  thinking: "ring-violet-400",
  worried: "ring-amber-300",
  angry: "ring-rose-400",
  excited: "ring-orange-400",
};

const emotionGlow: Record<Emotion, string> = {
  neutral: "shadow-violet-200/50",
  happy: "shadow-emerald-300/60",
  thinking: "shadow-violet-400/60",
  worried: "shadow-amber-300/60",
  angry: "shadow-rose-400/60",
  excited: "shadow-orange-300/60",
};

type PonyAgentProps = {
  agent: AgentConfig;
  isSpeaking: boolean;
  isTargeted?: boolean;
  bubblePlacement?: BubblePlacement;
  emotion?: Emotion;
  bubbleLabel?: string;
};

export function PonyAgent({
  agent,
  isSpeaking,
  isTargeted = false,
  bubblePlacement = "top",
  emotion = "neutral",
  bubbleLabel = "",
}: PonyAgentProps) {
  const showBubble = isSpeaking && !!bubbleLabel;
  const bubble = (
    <SpeechBubble
      text={bubbleLabel}
      visible={showBubble}
      placement={bubblePlacement}
      emotion={emotion}
    />
  );

  const ringClass = [
    "ring-[3px]",
    isSpeaking ? emotionRing[emotion] : "ring-white/70",
    isSpeaking ? emotionGlow[emotion] : "shadow-slate-200/60",
    isTargeted ? "ring-offset-2 ring-offset-amber-50 ring-amber-400" : "",
  ].join(" ");

  return (
    <div className="flex max-w-[min(100%,9rem)] flex-col items-center sm:max-w-none">
      <div className="relative flex flex-col items-center">
        {bubblePlacement === "top" ? bubble : null}

        <motion.div
          animate={
            isSpeaking
              ? { y: [0, -8, 0], scale: [1, 1.06, 1] }
              : { y: 0, scale: 1 }
          }
          transition={
            isSpeaking
              ? { duration: 1.6, repeat: Infinity, ease: "easeInOut" }
              : { duration: 0.3 }
          }
          className="relative"
        >
          {isSpeaking ? (
            <motion.div
              className="absolute -inset-3 rounded-full bg-violet-400/20 blur-md"
              animate={{ opacity: [0.3, 0.6, 0.3], scale: [0.95, 1.05, 0.95] }}
              transition={{ duration: 1.4, repeat: Infinity }}
            />
          ) : null}

          <div
            className={`relative flex h-[4.5rem] w-[4.5rem] items-center justify-center rounded-full bg-gradient-to-br sm:h-24 sm:w-24 ${agent.color} ${ringClass} shadow-xl`}
          >
            {isSpeaking ? (
              <motion.div
                className="absolute inset-0 rounded-full bg-white/25"
                animate={{ opacity: [0.15, 0.45, 0.15] }}
                transition={{ duration: 1.2, repeat: Infinity }}
              />
            ) : null}
            {isTargeted && !isSpeaking ? (
              <span className="absolute -inset-1.5 rounded-full border-2 border-dashed border-amber-400/80" />
            ) : null}
            <span
              className="relative text-3xl drop-shadow-sm sm:text-4xl"
              role="img"
              aria-label={agent.name}
            >
              {agent.emoji}
            </span>
          </div>
        </motion.div>

        {bubblePlacement === "bottom" ? bubble : null}
      </div>

      <div
        className={`mt-2.5 rounded-xl px-3 py-1.5 text-center transition-all sm:mt-3 ${
          isSpeaking
            ? "bg-white/90 shadow-md shadow-violet-100/80 ring-1 ring-violet-100"
            : "bg-white/50"
        }`}
      >
        <p
          className={`text-xs font-bold sm:text-sm ${
            isSpeaking ? "text-violet-900" : "text-slate-700"
          }`}
        >
          {agent.name}
        </p>
        <p className="text-[10px] text-slate-500 sm:text-xs">{agent.role}</p>
      </div>
    </div>
  );
}
