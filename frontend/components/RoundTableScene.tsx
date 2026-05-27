"use client";

import { useMemo, useState } from "react";
import { agents, mockEvents } from "@/lib/mockEvents";
import { getTargetRelationLine } from "@/lib/meetingUi";
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
  left: "col-start-1 row-start-2 justify-self-end pr-1 sm:pr-0",
  right: "col-start-3 row-start-2 justify-self-start pl-1 sm:pl-0",
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
    isComplete,
    start,
    pause,
    resume,
    replay,
    reset,
  } = useMeetingPlayer(mockEvents);

  const speakingId: AgentId | undefined =
    currentEvent?.type === "speech" ? currentEvent.speakerId : undefined;

  const targetId: AgentId | undefined =
    currentEvent?.type === "speech" ? currentEvent.targetId : undefined;

  const targetRelation = useMemo(() => {
    if (currentEvent?.type !== "speech") return undefined;
    return getTargetRelationLine(
      currentEvent.action,
      currentEvent.targetId,
      agents,
    );
  }, [currentEvent]);

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
    <div className="flex min-h-screen flex-col px-3 py-6 sm:px-4 sm:py-8">
      <header className="mb-4 text-center sm:mb-6">
        <h1 className="text-xl font-bold text-violet-900 sm:text-3xl">
          小马 AI 风格 · 专家圆桌
        </h1>
        <p className="mt-2 text-xs text-slate-600 sm:text-sm">
          Mock 播放 · 协议对齐 docs/meeting-event-spec.md
        </p>
      </header>

      <div className="relative mx-auto w-full max-w-3xl">
        <div className="grid grid-cols-3 grid-rows-3 gap-2 place-items-center overflow-visible sm:gap-4">
          <div className="col-start-2 row-start-2 flex h-28 w-28 items-center justify-center rounded-full border-4 border-amber-100 bg-gradient-to-br from-amber-50 to-orange-100 shadow-inner sm:h-36 sm:w-36">
            <span className="text-center text-[10px] font-medium text-amber-800/80 sm:text-xs">
              圆桌
            </span>
          </div>

          {agentsByPosition.map(({ agent, className }) => {
            const isSpeaking = speakingId === agent.id;
            const isTargeted = targetId === agent.id;

            return (
              <div key={agent.id} className={className}>
                <PonyAgent
                  agent={agent}
                  isSpeaking={isSpeaking}
                  isTargeted={isTargeted}
                  bubblePlacement={
                    agent.position === "top" ? "bottom" : "top"
                  }
                  emotion={
                    isSpeaking ? currentEvent?.emotion ?? "neutral" : "neutral"
                  }
                  action={isSpeaking ? currentEvent?.action : undefined}
                  speechText={isSpeaking ? currentEvent?.text ?? "" : ""}
                  targetRelation={isSpeaking ? targetRelation : undefined}
                />
              </div>
            );
          })}
        </div>
      </div>

      <div className="mt-8 space-y-4 sm:mt-10">
        {!hasStarted ? (
          <MeetingInput
            value={question}
            onChange={setQuestion}
            onSubmit={handleStart}
            disabled={isPlaying}
          />
        ) : (
          <div className="flex flex-wrap justify-center gap-2 sm:gap-3">
            {!isComplete ? (
              <button
                type="button"
                onClick={isPlaying ? pause : resume}
                className="rounded-xl border border-violet-200 bg-white px-4 py-2 text-sm font-medium text-violet-800 hover:bg-violet-50"
              >
                {isPlaying ? "暂停" : "继续"}
              </button>
            ) : (
              <button
                type="button"
                onClick={replay}
                className="rounded-xl border border-violet-300 bg-violet-50 px-4 py-2 text-sm font-medium text-violet-900 hover:bg-violet-100"
              >
                重新播放
              </button>
            )}
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
