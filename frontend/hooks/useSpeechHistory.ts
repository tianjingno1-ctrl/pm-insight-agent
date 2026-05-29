"use client";

import { useMemo } from "react";
import { agents } from "@/lib/mockEvents";
import type { SpeechMessage } from "@/lib/speechHistory";
import type { MeetingEvent } from "@/lib/types";

type UseSpeechHistoryOptions = {
  events: MeetingEvent[];
  currentEvent: MeetingEvent | null;
  currentEventId: string | null;
  activeIndex: number;
  streamedText: string;
  isPlaying: boolean;
  hasStarted: boolean;
  playbackKey: number;
};

export function useSpeechHistory({
  events,
  currentEvent,
  currentEventId,
  activeIndex,
  streamedText,
  isPlaying,
  hasStarted,
  playbackKey,
}: UseSpeechHistoryOptions): SpeechMessage[] {
  return useMemo(() => {
    if (!hasStarted || activeIndex < 0) {
      return [];
    }

    const messages: SpeechMessage[] = [];

    for (let i = 0; i <= activeIndex && i < events.length; i++) {
      const event = events[i];
      if (event.type !== "speech" || !event.speakerId || !event.text) {
        continue;
      }

      const agent = agents.find((a) => a.id === event.speakerId);
      if (!agent) continue;

      const fullText = event.text;
      const isCurrent = event.id === currentEventId;
      const isStreaming =
        isCurrent &&
        isPlaying &&
        currentEvent?.type === "speech" &&
        streamedText.length < fullText.length;

      const content =
        isCurrent && (isStreaming || streamedText.length > 0)
          ? isStreaming
            ? streamedText
            : streamedText.length >= fullText.length
              ? fullText
              : streamedText || fullText
          : fullText;

      messages.push({
        id: event.id,
        role: agent.id,
        roleName: agent.name,
        emoji: agent.emoji,
        color: agent.color,
        content,
        fullText,
        isStreaming,
      });
    }

    void playbackKey;
    return messages;
  }, [
    events,
    currentEvent,
    currentEventId,
    activeIndex,
    streamedText,
    isPlaying,
    hasStarted,
    playbackKey,
  ]);
}
