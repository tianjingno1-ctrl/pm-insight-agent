"use client";

import { useMemo, useState } from "react";
import { agents, mockEvents } from "@/lib/mockEvents";
import { useMeetingPlayer } from "@/hooks/useMeetingPlayer";
import type { AgentId } from "@/lib/types";
import { PonyAgent } from "./PonyAgent";
import { MeetingInput } from "./MeetingInput";
import { SummaryCard } from "./SummaryCard";

const positionClass: Record<
  "top" | "left" | "right" | "bottom",
  string
> = {
  top: "col-start-2 row-start-1 justify-self-center",
  left: "col-start-1 row-start-2 justify-self-end",
  right: "col-start-3 row-start-2 justify-self-start",
  bottom: "col-start-2 row-start-3 justify-self-center",
};

export function RoundTableScene() {
  const [question, setQuestion] = useState(
    "两周内 AI 财务助手 MVP 应该做什么？",
  );

  const {
    currentEvent,
    summary,
    isPlaying,
    hasStarted,
    start,
    pause,
    reset,
  } = useMeetingPlayer(mockEvents);

  const speakingId: AgentId | undefined =
    currentEvent?.type === "speech" ? currentEvent.speakerId : undefined;

  const agentsByPosition = useMemo(
    () =>
      agents.map((agent) => ({
        agent,
        className: positionClass[agent.position],
      })),
    [],
  );

  const handleStart = () => {
    if (!question.trim()) return;
    reset();
    start();
  };

  return (
    <div className="flex min-h-screen flex-col px-4 py-8">
      <header className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-violet-900 sm:text-3xl">
          小马 AI 风格 · 专家圆桌
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          Mock 播放 · 协议对齐 docs/meeting-event-spec.md
        </p>
      </header>

      <div className="relative mx-auto w-full max-w-3xl">
        <div className="grid grid-cols-3 grid-rows-3 gap-4 place-items-center">
          <div className="col-start-2 row-start-2 flex h-36 w-36 items-center justify-center rounded-full border-4 border-amber-100 bg-gradient-to-br from-amber-50 to-orange-100 shadow-inner">
            <span className="text-center text-xs font-medium text-amber-800/80">
              圆桌
            </span>
          </div>

          {agentsByPosition.map(({ agent, className }) => (
            <div key={agent.id} className={className}>
              <PonyAgent
                agent={agent}
                isSpeaking={speakingId === agent.id}
                emotion={
                  speakingId === agent.id ? currentEvent?.emotion : "neutral"
                }
                speechText={
                  speakingId === agent.id ? currentEvent?.text ?? "" : ""
                }
              />
            </div>
          ))}
        </div>
      </div>

      <div className="mt-10 space-y-4">
        {!hasStarted ? (
          <MeetingInput
            value={question}
            onChange={setQuestion}
            onSubmit={handleStart}
            disabled={isPlaying}
          />
        ) : (
          <div className="flex flex-wrap justify-center gap-3">
            <button
              type="button"
              onClick={isPlaying ? pause : start}
              disabled={!!summary}
              className="rounded-xl border border-violet-200 bg-white px-4 py-2 text-sm font-medium text-violet-800 hover:bg-violet-50 disabled:opacity-50"
            >
              {isPlaying ? "暂停" : "继续"}
            </button>
            <button
              type="button"
              onClick={reset}
              className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              重新开始
            </button>
          </div>
        )}

        {hasStarted && isPlaying ? (
          <p className="text-center text-xs text-slate-500">会议进行中…</p>
        ) : null}

        {summary ? <SummaryCard summary={summary} /> : null}
      </div>
    </div>
  );
}
