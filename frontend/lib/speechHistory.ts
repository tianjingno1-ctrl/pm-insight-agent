import type { AgentId } from "./types";

export type SpeechMessage = {
  id: string;
  role: AgentId;
  roleName: string;
  emoji: string;
  color: string;
  content: string;
  fullText: string;
  isStreaming: boolean;
};
