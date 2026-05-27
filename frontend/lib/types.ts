export type AgentId = "host" | "product" | "tech" | "growth";

export type Emotion =
  | "neutral"
  | "happy"
  | "thinking"
  | "worried"
  | "angry"
  | "excited";

export type MeetingAction =
  | "open"
  | "suggest"
  | "challenge"
  | "support"
  | "reject"
  | "summarize";

export type MeetingStage =
  | "opening"
  | "proposal"
  | "challenge"
  | "synthesis"
  | "closing";

export type MeetingEventType =
  | "meeting_started"
  | "speech"
  | "reaction"
  | "summary"
  | "meeting_done"
  | "error";

export type UiHint = {
  bubbleVariant?: "normal" | "warning" | "challenge" | "success";
  motion?: "pop" | "shake" | "bounce" | "glow";
  sound?: "none" | "pop" | "tap";
};

export type ErrorInfo = {
  code: string;
  message: string;
  recoverable: boolean;
};

export type MeetingSummary = {
  direction: string;
  disagreement: string;
  nextStep: string;
};

export type MeetingEvent = {
  id: string;
  type: MeetingEventType;

  speakerId?: AgentId;
  targetId?: AgentId;

  emotion?: Emotion;
  action?: MeetingAction;

  text?: string;

  duration_ms?: number;
  delay_before_ms?: number;

  summary?: MeetingSummary;

  stage?: MeetingStage;
  intensity?: 1 | 2 | 3 | 4 | 5;
  turnIndex?: number;
  roundIndex?: number;
  protocolVersion?: string;
  uiHint?: UiHint;
  errorInfo?: ErrorInfo;
};

export type AgentConfig = {
  id: AgentId;
  name: string;
  emoji: string;
  role: string;
  position: "top" | "left" | "right" | "bottom";
  color: string;
};
