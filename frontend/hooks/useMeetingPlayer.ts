"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { MeetingPlayer } from "@/lib/meeting-player";
import type { MeetingEvent } from "@/lib/types";

const DEFAULT_DELAY_MS = 300;
const DEFAULT_SPEECH_DURATION_MS = 2500;
const DEFAULT_REACTION_DURATION_MS = 800;

function controlDurationMs(event: MeetingEvent): number {
  return event.duration_ms ?? 0;
}

export function useMeetingPlayer(events: MeetingEvent[]): MeetingPlayer {
  const [currentEventId, setCurrentEventId] = useState<string | null>(null);
  const [summary, setSummary] = useState<MeetingPlayer["summary"]>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const indexRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const eventsRef = useRef(events);
  const playFromIndexRef = useRef<() => void>(() => {});

  useEffect(() => {
    eventsRef.current = events;
  }, [events]);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const schedule = useCallback(
    (fn: () => void, ms: number) => {
      clearTimer();
      timerRef.current = setTimeout(fn, ms);
    },
    [clearTimer],
  );

  const finishPlayback = useCallback(() => {
    clearTimer();
    setIsPlaying(false);
    setIsComplete(true);
    setCurrentEventId(null);
  }, [clearTimer]);

  const playFromIndex = useCallback(() => {
    const list = eventsRef.current;
    if (indexRef.current >= list.length) {
      finishPlayback();
      return;
    }

    const event = list[indexRef.current];
    const delay = event.delay_before_ms ?? DEFAULT_DELAY_MS;

    schedule(() => {
      const playingIndex = indexRef.current;
      setActiveIndex(playingIndex);

      switch (event.type) {
        case "summary": {
          if (event.summary) {
            setSummary(event.summary);
          }
          setCurrentEventId(null);
          indexRef.current += 1;
          setIsPlaying(false);
          setIsComplete(true);
          clearTimer();
          return;
        }

        case "meeting_done": {
          setCurrentEventId(null);
          indexRef.current += 1;
          setIsPlaying(false);
          setIsComplete(true);
          clearTimer();
          return;
        }

        case "error": {
          setCurrentEventId(event.id);
          setIsPlaying(false);
          setIsComplete(false);
          clearTimer();
          return;
        }

        case "meeting_started": {
          setCurrentEventId(null);
          indexRef.current += 1;
          schedule(() => playFromIndexRef.current(), controlDurationMs(event));
          return;
        }

        case "speech": {
          setCurrentEventId(event.id);
          indexRef.current += 1;
          schedule(
            () => playFromIndexRef.current(),
            event.duration_ms ?? DEFAULT_SPEECH_DURATION_MS,
          );
          return;
        }

        case "reaction": {
          setCurrentEventId(event.id);
          indexRef.current += 1;
          schedule(
            () => playFromIndexRef.current(),
            event.duration_ms ?? DEFAULT_REACTION_DURATION_MS,
          );
          return;
        }

        default: {
          indexRef.current += 1;
          schedule(() => playFromIndexRef.current(), 0);
        }
      }
    }, delay);
  }, [clearTimer, finishPlayback, schedule]);

  useEffect(() => {
    playFromIndexRef.current = playFromIndex;
  }, [playFromIndex]);

  const beginPlayback = useCallback(
    (options: { resetIndex: boolean }) => {
      clearTimer();
      if (options.resetIndex) {
        indexRef.current = 0;
        setActiveIndex(-1);
        setCurrentEventId(null);
        setSummary(null);
      }
      setIsComplete(false);
      setHasStarted(true);
      setIsPlaying(true);
      playFromIndex();
    },
    [clearTimer, playFromIndex],
  );

  const start = useCallback(() => {
    beginPlayback({ resetIndex: true });
  }, [beginPlayback]);

  const replay = useCallback(() => {
    beginPlayback({ resetIndex: true });
  }, [beginPlayback]);

  const resume = useCallback(() => {
    const list = eventsRef.current;
    if (indexRef.current >= list.length) {
      return;
    }
    setIsPlaying(true);
    setIsComplete(false);
    playFromIndex();
  }, [playFromIndex]);

  const pause = useCallback(() => {
    clearTimer();
    setIsPlaying(false);
  }, [clearTimer]);

  const reset = useCallback(() => {
    clearTimer();
    indexRef.current = 0;
    setActiveIndex(-1);
    setCurrentEventId(null);
    setSummary(null);
    setIsPlaying(false);
    setHasStarted(false);
    setIsComplete(false);
  }, [clearTimer]);

  useEffect(() => () => clearTimer(), [clearTimer]);

  const currentEvent = useMemo(
    () => events.find((e) => e.id === currentEventId) ?? null,
    [events, currentEventId],
  );

  return {
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
  };
}
