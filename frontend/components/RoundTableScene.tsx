"use client";

import { useMemo, useState } from "react";
import { agents, mockEvents } from "@/lib/mockEvents";
import { getTargetRelationLine } from "@/lib/meetingUi";
import {
  meetingSource,
  getMeetingPace,
  getMeetingScenario,
  getMeetingSseUrl,
  getMeetingTopic,
} from "@/lib/meetingSource";
import { useMeetingEventStream } from "@/hooks/useMeetingEventStream";
import { useMeetingPlayer } from "@/hooks/useMeetingPlayer";
import type { AgentId, MeetingEvent } from "@/lib/types";
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

const isSseSource = meetingSource === "sse";

export function RoundTableScene() {
  const [question, setQuestion] = useState(
    "两周内 AI 财务助手 MVP 应该做什么？",
  );

  const stream = useMeetingEventStream({
    url: getMeetingSseUrl(),
    scenario: getMeetingScenario(),
    pace: getMeetingPace(),
    topic: getMeetingTopic(),
    autoStart: isSseSource,
  });

  const eventsForPlayer: MeetingEvent[] = useMemo(() => {
    if (!isSseSource) {
      return mockEvents;
    }
    if (stream.status === "closed") {
      return stream.events;
    }
    return [];
  }, [stream.events, stream.status]);

  const layoutKey = isSseSource
    ? stream.status === "closed"
      ? "sse-ready"
      : "sse-pending"
    : "mock";

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
  } = useMeetingPlayer(eventsForPlayer);

  const sseStreamReady =
    isSseSource && stream.status === "closed" && stream.events.length > 0;

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
    if (isSseSource && !sseStreamReady) {
      return;
    }
    reset();
    start();
  };

  const inputDisabled =
    isPlaying ||
    (isSseSource &&
      (stream.status === "connecting" ||
        stream.status === "open" ||
        stream.status === "error"));

  const subtitle = isSseSource
    ? "SSE mock · 缓冲完成后播放 · docs/meeting-event-spec.md"
    : "Mock 播放 · 协议对齐 docs/meeting-event-spec.md";

  return (
    <div key={layoutKey} className="flex min-h-screen flex-col px-3 py-6 sm:px-4 sm:py-8">
      <header className="mb-4 text-center sm:mb-6">
        <h1 className="text-xl font-bold text-violet-900 sm:text-3xl">
          小马 AI 风格 · 专家圆桌
        </h1>
        <p className="mt-2 text-xs text-slate-600 sm:text-sm">{subtitle}</p>
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
        {isSseSource && stream.status === "connecting" ? (
          <p className="text-center text-xs text-slate-500">
            正在连接 mock SSE…
          </p>
        ) : null}
        {isSseSource && stream.status === "open" ? (
          <p className="text-center text-xs text-slate-500">
            正在接收会议事件…
          </p>
        ) : null}
        {isSseSource && stream.status === "error" ? (
          <p className="text-center text-xs text-rose-600">
            {stream.error ?? "SSE 加载失败，请确认 backend :8000 已启动"}
          </p>
        ) : null}

        {!hasStarted ? (
          <MeetingInput
            value={question}
            onChange={setQuestion}
            onSubmit={handleStart}
            disabled={inputDisabled}
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
