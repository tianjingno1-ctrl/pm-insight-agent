"use client";

import { useEffect, useRef } from "react";
import type { SpeechMessage } from "@/lib/speechHistory";

type SpeechHistoryPanelProps = {
  messages: SpeechMessage[];
  visible: boolean;
  isPlaying: boolean;
  className?: string;
};

const ROLE_ACCENT: Record<string, string> = {
  host: "border-l-violet-400",
  product: "border-l-sky-400",
  tech: "border-l-emerald-400",
  growth: "border-l-orange-400",
};

function MessageCard({ message }: { message: SpeechMessage }) {
  const showCursor =
    message.isStreaming && message.content.length < message.fullText.length;
  const accent = ROLE_ACCENT[message.role] ?? "border-l-violet-300";

  return (
    <div
      className={`flex gap-3 rounded-xl border border-white/60 bg-white/80 p-3 shadow-sm transition-shadow ${
        message.isStreaming ? "shadow-md shadow-violet-100/80 ring-1 ring-violet-100" : ""
      }`}
    >
      <span
        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-gradient-to-br text-lg shadow-sm ring-2 ring-white ${message.color}`}
        aria-hidden
      >
        {message.emoji}
      </span>
      <div className={`min-w-0 flex-1 border-l-2 pl-3 ${accent}`}>
        <p className="text-xs font-bold text-slate-800">{message.roleName}</p>
        <p className="mt-1.5 text-sm leading-relaxed text-slate-600">
          {message.content}
          {showCursor ? (
            <span className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-violet-500 align-middle" />
          ) : null}
        </p>
      </div>
    </div>
  );
}

export function SpeechHistoryPanel({
  messages,
  visible,
  isPlaying,
  className = "",
}: SpeechHistoryPanelProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  return (
    <aside
      className={`flex flex-col ${className}`}
      aria-live="polite"
      aria-label="发言记录"
    >
      <div className="glass-panel-strong mb-3 flex items-center justify-between rounded-2xl px-4 py-3">
        <div className="flex items-center gap-2">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-violet-100 text-sm">
            💬
          </span>
          <div>
            <p className="text-sm font-bold text-slate-800">发言记录</p>
            <p className="text-[10px] text-slate-500">全部专家发言汇总</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isPlaying ? (
            <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-medium text-emerald-700">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
              LIVE
            </span>
          ) : null}
          {messages.length > 0 ? (
            <span className="rounded-full bg-violet-100 px-2.5 py-1 text-[10px] font-semibold text-violet-700">
              {messages.length} 条
            </span>
          ) : null}
        </div>
      </div>

      <div className="speech-scroll glass-panel flex max-h-[22rem] min-h-[14rem] flex-1 flex-col overflow-y-auto rounded-2xl p-3 sm:max-h-[32rem] sm:min-h-[18rem] sm:p-4">
        {!visible ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 py-8 text-center">
            <span className="text-3xl opacity-40">🪑</span>
            <p className="text-sm text-slate-400">
              开始讨论后
              <br />
              所有专家发言将在此汇总
            </p>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-1 flex-col items-center justify-center gap-2 py-8">
            <span className="inline-flex gap-1">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="h-2 w-2 animate-bounce rounded-full bg-violet-300"
                  style={{ animationDelay: `${i * 0.15}s` }}
                />
              ))}
            </span>
            <p className="text-sm text-slate-400">等待第一位发言…</p>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            {messages.map((message) => (
              <MessageCard key={message.id} message={message} />
            ))}
            <div ref={bottomRef} className="h-px shrink-0" />
          </div>
        )}
      </div>
    </aside>
  );
}
