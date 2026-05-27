"use client";

import { motion, AnimatePresence } from "framer-motion";

type SpeechBubbleProps = {
  text: string;
  visible: boolean;
};

export function SpeechBubble({ text, visible }: SpeechBubbleProps) {
  return (
    <AnimatePresence>
      {visible && text ? (
        <motion.div
          key={text}
          initial={{ opacity: 0, scale: 0.85, y: 8 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.9, y: 4 }}
          transition={{ type: "spring", stiffness: 420, damping: 28 }}
          className="absolute bottom-full left-1/2 z-20 mb-3 w-[min(280px,70vw)] -translate-x-1/2"
        >
          <div className="rounded-2xl border border-white/80 bg-white/95 px-4 py-3 text-sm leading-relaxed text-slate-800 shadow-lg shadow-violet-200/40">
            <p>{text}</p>
            <div className="absolute -bottom-2 left-1/2 h-4 w-4 -translate-x-1/2 rotate-45 border-b border-r border-white/80 bg-white/95" />
          </div>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
