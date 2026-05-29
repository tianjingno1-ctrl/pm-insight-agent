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
import { useSpeechHistory } from "@/hooks/useSpeechHistory";
import { useStreamingText } from "@/hooks/useStreamingText";
import type { AgentId, MeetingEvent } from "@/lib/types";
import { PonyAgent } from "./PonyAgent";
import { MeetingInput } from "./MeetingInput";
import { SummaryCard } from "./SummaryCard";
import { SpeechHistoryPanel } from "./SpeechHistoryPanel";

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
  const [playbackKey, setPlaybackKey] = useState(0);
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
    currentEventId,
    activeIndex,
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

  const isSpeechPlaying =
    isPlaying && currentEvent?.type === "speech";

  const streamedText = useStreamingText(
    streamSpeechText,
    isSpeechPlaying,
    currentEvent?.type === "speech" ? currentEvent.duration_ms : undefined,
  );

  const speechMessages = useSpeechHistory({
    events: eventsForPlayer,
    currentEvent,
    currentEventId,
    activeIndex,
    streamedText,
    isPlaying,
    hasStarted,
    playbackKey,
  });

  const showHistoryPanel = hasStarted;

  const bumpPlayback = () => setPlaybackKey((k) => k + 1);

  const handleReplay = () => {
    bumpPlayback();
    replay();
  };

  const handleReset = () => {
    reset();
    bumpPlayback();
  };

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
    bumpPlayback();
    start();
  };

  useEffect(() => {
    if (!pendingPlayRef.current || !sseStreamReady) {
      return;
    }
    pendingPlayRef.current = false;
    bumpPlayback();
    start();
  }, [sseStreamReady, start]);

  const inputDisabled =
    isPlaying ||
    (isSseSource &&
      (stream.status === "connecting" ||
        stream.status === "open" ||
        (stream.status === "error" && isLlmScenario)));

  const subtitle = isSseSource
    ? isLlmScenario
      ? "AI 多专家圆桌 · DeepSeek 驱动 · 输入议题即可开始"
      : "AI 多专家圆桌 · 演示模式"
    : "AI 多专家圆桌 · 本地演示";

  const statusBadge = !hasStarted
    ? isSseSource && stream.status === "connecting"
      ? { text: "正在生成讨论脚本…", tone: "loading" as const }
      : isSseSource && stream.status === "open"
        ? { text: "正在接收结果…", tone: "loading" as const }
        : isSseSource && stream.status === "error"
          ? { text: "连接失败", tone: "error" as const }
          : { text: "就绪", tone: "ready" as const }
    : isPlaying
      ? { text: "讨论进行中", tone: "live" as const }
      : isComplete
        ? { text: "讨论结束", tone: "done" as const }
        : { text: "已暂停", tone: "pause" as const };

  const badgeStyles = {
    ready: "bg-violet-100 text-violet-700",
    loading: "bg-amber-100 text-amber-700",
    live: "bg-emerald-100 text-emerald-700",
    done: "bg-sky-100 text-sky-700",
    pause: "bg-slate-100 text-slate-600",
    error: "bg-rose-100 text-rose-700",
  };

  return (
    <div key={layoutKey} className="flex min-h-screen flex-col px-3 py-5 sm:px-6 sm:py-8">
      <header className="mx-auto mb-6 w-full max-w-6xl text-center sm:mb-8">
        <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-white/70 px-4 py-1.5 text-xs font-medium text-violet-700 shadow-sm ring-1 ring-violet-100">
          <span>✨</span>
          <span>PM Insight Agent</span>
        </div>
        <h1 className="bg-gradient-to-r from-violet-900 via-violet-700 to-fuchsia-600 bg-clip-text text-2xl font-extrabold tracking-tight text-transparent sm:text-4xl">
          AI 专家圆桌
        </h1>
        <p className="mt-2 text-sm text-slate-600">{subtitle}</p>
        <div className="mt-3 flex flex-wrap justify-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${badgeStyles[statusBadge.tone]}`}
          >
            {statusBadge.tone === "live" ? (
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-500" />
            ) : null}
            {statusBadge.tone === "loading" ? (
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-amber-500" />
            ) : null}
            {statusBadge.text}
          </span>
          {(hasStarted || question.trim()) && (
            <span className="inline-flex max-w-md items-center rounded-full bg-white/80 px-3 py-1 text-xs text-slate-600 shadow-sm ring-1 ring-violet-100">
              议题：{question.trim()}
            </span>
          )}
        </div>
      </header>

      <div className="mx-auto flex w-full max-w-6xl flex-col gap-5 lg:flex-row lg:items-stretch lg:gap-6">
        <SpeechHistoryPanel
          className="order-2 w-full lg:order-1 lg:w-[340px] lg:shrink-0 xl:w-[380px]"
          messages={speechMessages}
          visible={showHistoryPanel}
          isPlaying={isSpeechPlaying}
        />

        <div className="glass-panel-strong order-1 flex flex-1 flex-col rounded-3xl p-4 sm:p-6 lg:order-2">
          <div className="relative mx-auto w-full max-w-lg flex-1">
            {/* Table surface */}
            <div className="pointer-events-none absolute left-1/2 top-1/2 h-[55%] w-[55%] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-br from-amber-100/80 via-orange-50/60 to-amber-50/40 shadow-inner ring-1 ring-amber-200/50" />
            <div className="pointer-events-none absolute left-1/2 top-1/2 h-[38%] w-[38%] -translate-x-1/2 -translate-y-1/2 rounded-full border border-dashed border-amber-300/40" />

            <div className="relative grid grid-cols-3 grid-rows-3 gap-1 place-items-center overflow-visible py-4 sm:gap-2 sm:py-6">
              <div className="col-start-2 row-start-2 flex h-24 w-24 flex-col items-center justify-center rounded-full border-4 border-amber-200/80 bg-gradient-to-br from-amber-50 via-orange-50 to-amber-100 shadow-lg shadow-amber-200/40 sm:h-32 sm:w-32">
                <span className="text-2xl sm:text-3xl" aria-hidden>
                  🪑
                </span>
                <span className="mt-0.5 text-[10px] font-bold text-amber-800/70 sm:text-xs">
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
                        isSpeaking
                          ? (currentEvent?.emotion ?? "neutral")
                          : "neutral"
                      }
                      bubbleLabel={isSpeaking ? bubbleLabel : ""}
                    />
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      <div className="mx-auto mt-8 w-full max-w-3xl space-y-5 sm:mt-10">
        {isSseSource && stream.status === "error" ? (
          <p className="text-center text-sm text-rose-600">
            {stream.error ?? "无法连接后端，请确认服务已启动（端口 8000）"}
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
          <div className="flex flex-wrap justify-center gap-3">
            {!isComplete ? (
              <button
                type="button"
                onClick={isPlaying ? pause : resume}
                className="glass-panel-strong rounded-2xl px-6 py-2.5 text-sm font-semibold text-violet-800 transition hover:shadow-md"
              >
                {isPlaying ? "⏸ 暂停" : "▶ 继续"}
              </button>
            ) : (
              <button
                type="button"
                onClick={handleReplay}
                className="rounded-2xl bg-gradient-to-r from-violet-600 to-fuchsia-500 px-6 py-2.5 text-sm font-semibold text-white shadow-md shadow-violet-300/40 transition hover:brightness-105"
              >
                ↺ 重新播放
              </button>
            )}
            <button
              type="button"
              onClick={handleReset}
              className="rounded-2xl border border-slate-200/80 bg-white/80 px-6 py-2.5 text-sm font-semibold text-slate-600 transition hover:bg-white"
            >
              重新开始
            </button>
          </div>
        )}

        {summary ? <SummaryCard summary={summary} /> : null}
      </div>
    </div>
  );
}
