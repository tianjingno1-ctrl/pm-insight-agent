"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MeetingEvent, MeetingSummary } from "@/lib/types";

const DEFAULT_DELAY = 300;
const DEFAULT_DURATION = 2500;

export function useMeetingPlayer(events: MeetingEvent[]) {
  const [currentEventId, setCurrentEventId] = useState<string | null>(null);
  const [summary, setSummary] = useState<MeetingSummary | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);

  const indexRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const eventsRef = useRef(events);

  useEffect(() => {
    eventsRef.current = events;
  }, [events]);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const schedule = useCallback((fn: () => void, ms: number) => {
    clearTimer();
    timerRef.current = setTimeout(fn, ms);
  }, [clearTimer]);

  const playFromIndex = useCallback(() => {
    const list = eventsRef.current;
    if (indexRef.current >= list.length) {
      setIsPlaying(false);
      return;
    }

    const event = list[indexRef.current];
    const delay = event.delay_before_ms ?? DEFAULT_DELAY;

    schedule(() => {
      setCurrentEventId(event.id);

      if (event.type === "summary" && event.summary) {
        setSummary(event.summary);
        indexRef.current += 1;
        setIsPlaying(false);
        return;
      }

      const duration = event.duration_ms ?? DEFAULT_DURATION;
      indexRef.current += 1;

      schedule(() => {
        playFromIndex();
      }, duration);
    }, delay);
  }, [schedule]);

  const start = useCallback(() => {
    clearTimer();
    indexRef.current = 0;
    setCurrentEventId(null);
    setSummary(null);
    setHasStarted(true);
    setIsPlaying(true);
    playFromIndex();
  }, [clearTimer, playFromIndex]);

  const pause = useCallback(() => {
    clearTimer();
    setIsPlaying(false);
  }, [clearTimer]);

  const reset = useCallback(() => {
    clearTimer();
    indexRef.current = 0;
    setCurrentEventId(null);
    setSummary(null);
    setIsPlaying(false);
    setHasStarted(false);
  }, [clearTimer]);

  useEffect(() => () => clearTimer(), [clearTimer]);

  const currentEvent = useMemo(
    () => events.find((e) => e.id === currentEventId) ?? null,
    [events, currentEventId],
  );

  return {
    currentEvent,
    currentEventId,
    summary,
    isPlaying,
    hasStarted,
    start,
    pause,
    reset,
  };
}
