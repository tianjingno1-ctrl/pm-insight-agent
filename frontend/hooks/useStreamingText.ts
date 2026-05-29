"use client";

import { useEffect, useRef, useState } from "react";

const DEFAULT_DURATION_MS = 2500;
const MIN_TICK_MS = 35;
const MAX_TICK_MS = 100;

export function useStreamingText(
  text: string,
  isPlaying: boolean,
  durationMs?: number,
): string {
  const [prevText, setPrevText] = useState(text);
  const [charIndex, setCharIndex] = useState(0);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  if (text !== prevText) {
    setPrevText(text);
    setCharIndex(0);
  }

  useEffect(() => {
    const clearTimer = () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };

    if (!text || !isPlaying) {
      clearTimer();
      return clearTimer;
    }

    const chars = Array.from(text);
    const totalMs = durationMs ?? DEFAULT_DURATION_MS;
    const tickMs = Math.max(
      MIN_TICK_MS,
      Math.min(MAX_TICK_MS, totalMs / Math.max(chars.length, 1)),
    );

    clearTimer();
    timerRef.current = setInterval(() => {
      setCharIndex((current) => {
        if (current >= chars.length) {
          clearTimer();
          return current;
        }
        const next = current + 1;
        if (next >= chars.length) {
          clearTimer();
        }
        return next;
      });
    }, tickMs);

    return clearTimer;
  }, [text, isPlaying, durationMs]);

  if (!text) {
    return "";
  }

  return Array.from(text)
    .slice(0, charIndex)
    .join("");
}
