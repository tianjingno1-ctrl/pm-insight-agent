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

export type MeetingSummary = {
  direction: string;
  disagreement: string;
  nextStep: string;
};

export type MeetingEvent = {
  id: string;
  type: "speech" | "reaction" | "summary";

  speakerId?: AgentId;
  targetId?: AgentId;

  emotion?: Emotion;
  action?: MeetingAction;

  text?: string;

  duration_ms?: number;
  delay_before_ms?: number;

  summary?: MeetingSummary;
};

export type AgentConfig = {
  id: AgentId;
  name: string;
  emoji: string;
  role: string;
  position: "top" | "left" | "right" | "bottom";
  color: string;
};
