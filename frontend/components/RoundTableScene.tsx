"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { agents, mockEvents } from "@/lib/mockEvents";
import { getShortBubbleText } from "@/lib/meetingUi";
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
import { SpeechStreamPanel } from "./SpeechStreamPanel";

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
const meetingScenario = getMeetingScenario();
const isLlmScenario = meetingScenario === "llm";
const defaultQuestion =
  getMeetingTopic() ?? "两周内 AI 财务助手 MVP 应该做什么？";

export function RoundTableScene() {
  const [question, setQuestion] = useState(defaultQuestion);
  const pendingPlayRef = useRef(false);

  const stream = useMeetingEventStream({
    url: getMeetingSseUrl(),
    scenario: meetingScenario,
    pace: getMeetingPace(),
    topic: getMeetingTopic(),
    // LLM 议题由用户点击「开始讨论」时传入；预设 SSE 场景仍在挂载时预拉取
    autoStart: isSseSource && !isLlmScenario,
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

  const speakingAgent = useMemo(
    () => (speakingId ? agents.find((a) => a.id === speakingId) : undefined),
    [speakingId],
  );

  const bubbleLabel = useMemo(() => {
    if (currentEvent?.type !== "speech") return "";
    return getShortBubbleText(
      currentEvent.action,
      currentEvent.targetId,
      agents,
    );
  }, [currentEvent]);

  const streamSpeechText =
    currentEvent?.type === "speech" ? (currentEvent.text ?? "") : "";

  const showStreamPanel = hasStarted;

  const agentsByPosition = useMemo(
    () =>
      agents.map((agent) => ({
        agent,
        className: positionClass[agent.position],
      })),
    [],
  );

  const handleStart = () => {
    const topic = question.trim();
    if (!topic) return;

    if (isSseSource && isLlmScenario) {
      pendingPlayRef.current = true;
      stream.reset();
      stream.start({ topic });
      return;
    }

    if (isSseSource && !sseStreamReady) {
      return;
    }
    reset();
    start();
  };

  useEffect(() => {
    if (!pendingPlayRef.current || !sseStreamReady) {
      return;
    }
    pendingPlayRef.current = false;
    reset();
    start();
  }, [sseStreamReady, reset, start]);

  const inputDisabled =
    isPlaying ||
    (isSseSource &&
      (stream.status === "connecting" ||
        stream.status === "open" ||
        (stream.status === "error" && isLlmScenario)));

  const subtitle = isSseSource
    ? isLlmScenario
      ? "DeepSeek 圆桌 · 输入议题后生成 · 失败自动 fallback"
      : "SSE mock · 缓冲完成后播放 · docs/meeting-event-spec.md"
    : "Mock 播放 · 协议对齐 docs/meeting-event-spec.md";

  return (
    <div key={layoutKey} className="flex min-h-screen flex-col px-3 py-6 sm:px-4 sm:py-8">
      <header className="mb-4 text-center sm:mb-6">
        <h1 className="text-xl font-bold text-violet-900 sm:text-3xl">
          小马 AI 风格 · 专家圆桌
        </h1>
        <p className="mt-2 text-xs text-slate-600 sm:text-sm">{subtitle}</p>
      </header>

      <div className="mx-auto flex w-full max-w-5xl flex-col gap-4 lg:flex-row lg:items-start lg:gap-6">
        <SpeechStreamPanel
          className="order-2 w-full lg:order-1 lg:w-64 lg:shrink-0 xl:w-72"
          speaker={speakingAgent}
          emotion={
            currentEvent?.type === "speech"
              ? (currentEvent.emotion ?? "neutral")
              : "neutral"
          }
          fullText={streamSpeechText}
          visible={showStreamPanel}
          isPlaying={isPlaying && currentEvent?.type === "speech"}
          durationMs={
            currentEvent?.type === "speech"
              ? currentEvent.duration_ms
              : undefined
          }
        />

        <div className="relative order-1 flex-1 lg:order-2">
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
                  bubbleLabel={isSpeaking ? bubbleLabel : ""}
                />
              </div>
            );
          })}
        </div>
        </div>
      </div>

      <div className="mt-8 space-y-4 sm:mt-10">
        {isSseSource && stream.status === "connecting" ? (
          <p className="text-center text-xs text-slate-500">
            {isLlmScenario
              ? "正在调用 DeepSeek 生成圆桌脚本…"
              : "正在连接 mock SSE…"}
          </p>
        ) : null}
        {isSseSource && stream.status === "open" ? (
          <p className="text-center text-xs text-slate-500">
            {isLlmScenario ? "正在接收生成结果…" : "正在接收会议事件…"}
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
