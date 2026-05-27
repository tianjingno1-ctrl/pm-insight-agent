import type { MeetingEvent, MeetingSummary } from "./types";

export interface MeetingPlayer {
  currentEvent: MeetingEvent | null;
  currentEventId: string | null;
  summary: MeetingSummary | null;
  isPlaying: boolean;
  hasStarted: boolean;
  isComplete: boolean;
  start: () => void;
  pause: () => void;
  resume: () => void;
  replay: () => void;
  reset: () => void;
}
