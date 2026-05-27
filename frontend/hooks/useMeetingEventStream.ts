"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { MeetingEvent, MeetingEventType } from "@/lib/types";

const MEETING_EVENT_TYPES: MeetingEventType[] = [
  "meeting_started",
  "speech",
  "reaction",
  "summary",
  "meeting_done",
  "error",
];

const DEFAULT_STREAM_URL = "http://127.0.0.1:8000/api/meetings/mock-stream";

export type MeetingStreamStatus =
  | "idle"
  | "connecting"
  | "open"
  | "closed"
  | "error";

export type UseMeetingEventStreamOptions = {
  url?: string;
  scenario?: string;
  pace?: number;
  autoStart?: boolean;
};

export type UseMeetingEventStreamResult = {
  events: MeetingEvent[];
  status: MeetingStreamStatus;
  error: string | null;
  start: () => void;
  stop: () => void;
  reset: () => void;
  isStreaming: boolean;
};

function isMeetingEventType(value: unknown): value is MeetingEventType {
  return (
    typeof value === "string" &&
    MEETING_EVENT_TYPES.includes(value as MeetingEventType)
  );
}

function parseMeetingEvent(data: string): MeetingEvent {
  const raw: unknown = JSON.parse(data);
  if (!raw || typeof raw !== "object") {
    throw new Error("SSE payload is not an object");
  }
  const record = raw as Record<string, unknown>;
  if (typeof record.id !== "string" || !isMeetingEventType(record.type)) {
    throw new Error("SSE payload missing id or type");
  }
  return raw as MeetingEvent;
}

function buildStreamUrl(
  baseUrl: string,
  scenario: string,
  pace: number,
): string {
  const url = new URL(baseUrl);
  url.searchParams.set("scenario", scenario);
  url.searchParams.set("pace", String(pace));
  return url.toString();
}

export function useMeetingEventStream(
  options: UseMeetingEventStreamOptions = {},
): UseMeetingEventStreamResult {
  const {
    url = DEFAULT_STREAM_URL,
    scenario = "default",
    pace = 1.0,
    autoStart = false,
  } = options;

  const [events, setEvents] = useState<MeetingEvent[]>([]);
  const [status, setStatus] = useState<MeetingStreamStatus>("idle");
  const [error, setError] = useState<string | null>(null);

  const sourceRef = useRef<EventSource | null>(null);
  const optionsRef = useRef({ url, scenario, pace });
  optionsRef.current = { url, scenario, pace };

  const closeSource = useCallback(() => {
    if (sourceRef.current) {
      sourceRef.current.close();
      sourceRef.current = null;
    }
  }, []);

  const stop = useCallback(() => {
    closeSource();
    setStatus((prev) => (prev === "error" ? "error" : "closed"));
  }, [closeSource]);

  const reset = useCallback(() => {
    closeSource();
    setEvents([]);
    setError(null);
    setStatus("idle");
  }, [closeSource]);

  const start = useCallback(() => {
    closeSource();
    setEvents([]);
    setError(null);
    setStatus("connecting");

    const { url: streamUrl, scenario: sc, pace: p } = optionsRef.current;
    const source = new EventSource(buildStreamUrl(streamUrl, sc, p));
    sourceRef.current = source;

    source.onopen = () => {
      setStatus("open");
    };

    source.onmessage = (message) => {
      try {
        const event = parseMeetingEvent(message.data);
        setEvents((prev) => [...prev, event]);
        if (event.type === "meeting_done" || event.type === "error") {
          closeSource();
          setStatus(event.type === "error" ? "error" : "closed");
          if (event.type === "error" && event.errorInfo?.message) {
            setError(event.errorInfo.message);
          }
        }
      } catch (err) {
        closeSource();
        setStatus("error");
        setError(err instanceof Error ? err.message : "Failed to parse SSE event");
      }
    };

    source.onerror = () => {
      if (sourceRef.current !== source) {
        return;
      }
      closeSource();
      setStatus((prev) => {
        if (prev === "closed") {
          return prev;
        }
        return "error";
      });
      setError((prev) => prev ?? "SSE connection failed");
    };
  }, [closeSource]);

  useEffect(() => {
    if (autoStart) {
      start();
    }
    return () => {
      closeSource();
    };
  }, [autoStart, start, closeSource]);

  const isStreaming = status === "connecting" || status === "open";

  return {
    events,
    status,
    error,
    start,
    stop,
    reset,
    isStreaming,
  };
}
