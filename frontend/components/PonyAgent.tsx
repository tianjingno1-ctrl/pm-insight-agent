"use client";

import { motion } from "framer-motion";
import type { AgentConfig, Emotion } from "@/lib/types";
import { SpeechBubble } from "./SpeechBubble";

const emotionRing: Record<Emotion, string> = {
  neutral: "ring-slate-200",
  happy: "ring-amber-300",
  thinking: "ring-violet-300",
  worried: "ring-orange-300",
  angry: "ring-rose-400",
  excited: "ring-sky-300",
};

type PonyAgentProps = {
  agent: AgentConfig;
  isSpeaking: boolean;
  emotion?: Emotion;
  speechText?: string;
};

export function PonyAgent({
  agent,
  isSpeaking,
  emotion = "neutral",
  speechText = "",
}: PonyAgentProps) {
  return (
    <div className="relative flex flex-col items-center">
      <SpeechBubble text={speechText} visible={isSpeaking && !!speechText} />

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
        className={`relative flex h-24 w-24 items-center justify-center rounded-full bg-gradient-to-br ${agent.color} ring-4 ${emotionRing[emotion]} shadow-lg ${
          isSpeaking ? "shadow-violet-300/60" : "shadow-slate-200/80"
        }`}
      >
        {isSpeaking ? (
          <motion.div
            className="absolute inset-0 rounded-full bg-white/30"
            animate={{ opacity: [0.2, 0.5, 0.2] }}
            transition={{ duration: 1.2, repeat: Infinity }}
          />
        ) : null}
        <span className="text-4xl" role="img" aria-label={agent.name}>
          {agent.emoji}
        </span>
      </motion.div>

      <div className="mt-3 text-center">
        <p className="text-sm font-semibold text-slate-800">{agent.name}</p>
        <p className="text-xs text-slate-500">{agent.role}</p>
      </div>
    </div>
  );
}
