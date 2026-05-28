"use client";

import { motion, AnimatePresence } from "framer-motion";
import type { AgentConfig, Emotion } from "@/lib/types";
import { EMOTION_BUBBLE_STYLES } from "@/lib/meetingUi";
import { useStreamingText } from "@/hooks/useStreamingText";

type SpeechStreamPanelProps = {
  speaker?: AgentConfig;
  emotion?: Emotion;
  fullText: string;
  visible: boolean;
  isPlaying: boolean;
  durationMs?: number;
  className?: string;
};

type StreamingTextContentProps = {
  fullText: string;
  isPlaying: boolean;
  durationMs?: number;
  className?: string;
};

function StreamingTextContent({
  fullText,
  isPlaying,
  durationMs,
  className = "",
}: StreamingTextContentProps) {
  const streamed = useStreamingText(fullText, isPlaying, durationMs);

  return (
    <p className={className}>
      {streamed}
      {isPlaying && streamed.length < fullText.length ? (
        <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-violet-400 align-middle" />
      ) : null}
    </p>
  );
}

export function SpeechStreamPanel({
  speaker,
  emotion = "neutral",
  fullText,
  visible,
  isPlaying,
  durationMs,
  className = "",
}: SpeechStreamPanelProps) {
  const style = EMOTION_BUBBLE_STYLES[emotion];

  return (
    <aside
      className={`flex flex-col ${className}`}
      aria-live="polite"
      aria-label="发言流式输出"
    >
      <div className="mb-2 flex items-center gap-2 px-1">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-violet-600/80">
          发言区
        </span>
        {isPlaying ? (
          <span className="inline-flex items-center gap-1 text-[10px] text-slate-400">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
            流式输出中
          </span>
        ) : null}
      </div>

      <div className="min-h-[12rem] flex-1 rounded-2xl border border-violet-100/80 bg-white/70 p-4 shadow-inner backdrop-blur-sm sm:min-h-[16rem] sm:p-5">
        <AnimatePresence mode="wait">
          {visible && speaker && fullText ? (
            <motion.div
              key={speaker.id + fullText.slice(0, 24)}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2 }}
            >
              <div className="mb-3 flex items-center gap-2 border-b border-violet-50 pb-3">
                <span
                  className={`flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br text-lg shadow-sm ${speaker.color}`}
                >
                  {speaker.emoji}
                </span>
                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    {speaker.name}
                  </p>
                  <p className="text-[11px] text-slate-500">{speaker.role}</p>
                </div>
              </div>

              <StreamingTextContent
                key={`${speaker.id}-${fullText}`}
                fullText={fullText}
                isPlaying={isPlaying}
                durationMs={durationMs}
                className={`text-sm leading-relaxed sm:text-[15px] ${style.panel.includes("text-") ? "" : "text-slate-700"}`}
              />
            </motion.div>
          ) : (
            <motion.p
              key="placeholder"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="text-sm leading-relaxed text-slate-400"
            >
              {visible ? "等待下一位发言…" : "开始讨论后，完整发言将在此流式显示"}
            </motion.p>
          )}
        </AnimatePresence>
      </div>
    </aside>
  );
}
