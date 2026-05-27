"use client";

import { motion } from "framer-motion";
import type { AgentConfig, Emotion, MeetingAction } from "@/lib/types";
import { SpeechBubble } from "./SpeechBubble";

const emotionRing: Record<Emotion, string> = {
  neutral: "ring-slate-200",
  happy: "ring-emerald-300",
  thinking: "ring-violet-300",
  worried: "ring-amber-300",
  angry: "ring-rose-400",
  excited: "ring-orange-300",
};

type PonyAgentProps = {
  agent: AgentConfig;
  isSpeaking: boolean;
  isTargeted?: boolean;
  emotion?: Emotion;
  action?: MeetingAction;
  speechText?: string;
  targetRelation?: string;
};

export function PonyAgent({
  agent,
  isSpeaking,
  isTargeted = false,
  emotion = "neutral",
  action,
  speechText = "",
  targetRelation,
}: PonyAgentProps) {
  const showBubble = isSpeaking && !!speechText;

  const ringClass = [
    "ring-4",
    isSpeaking ? emotionRing[emotion] : "ring-slate-200/80",
    isSpeaking ? "shadow-violet-300/60" : "shadow-slate-200/80",
    isTargeted ? "ring-offset-2 ring-offset-amber-100/80 ring-amber-400" : "",
  ].join(" ");

  return (
    <div className="relative flex max-w-[min(100%,9rem)] flex-col items-center sm:max-w-none">
      <SpeechBubble
        text={speechText}
        visible={showBubble}
        emotion={emotion}
        action={action}
        targetRelation={targetRelation}
      />

      <motion.div
        animate={
          isSpeaking
            ? { y: [0, -6, 0], scale: [1, 1.04, 1] }
            : { y: 0, scale: 1 }
        }
        transition={
          isSpeaking
            ? { duration: 1.6, repeat: Infinity, ease: "easeInOut" }
            : { duration: 0.3 }
        }
        className={`relative flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br sm:h-24 sm:w-24 ${agent.color} ${ringClass} shadow-lg`}
      >
        {isSpeaking ? (
          <motion.div
            className="absolute inset-0 rounded-full bg-white/30"
            animate={{ opacity: [0.2, 0.5, 0.2] }}
            transition={{ duration: 1.2, repeat: Infinity }}
          />
        ) : null}
        {isTargeted && !isSpeaking ? (
          <span className="absolute -inset-1 rounded-full border-2 border-dashed border-amber-400/70" />
        ) : null}
        <span className="relative text-3xl sm:text-4xl" role="img" aria-label={agent.name}>
          {agent.emoji}
        </span>
      </motion.div>

      <div className="mt-2 text-center sm:mt-3">
        <p className="text-xs font-semibold text-slate-800 sm:text-sm">{agent.name}</p>
        <p className="text-[10px] text-slate-500 sm:text-xs">{agent.role}</p>
      </div>
    </div>
  );
}
