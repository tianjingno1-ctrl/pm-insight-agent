import type { AgentConfig, Emotion, MeetingAction } from "./types";

export const ACTION_LABELS: Record<MeetingAction, string> = {
  open: "开场",
  suggest: "提议",
  challenge: "质疑",
  support: "支持",
  reject: "反对",
  summarize: "收束",
};

const TARGET_VERB: Partial<Record<MeetingAction, string>> = {
  challenge: "质疑了",
  reject: "反对了",
  support: "支持了",
  suggest: "回应了",
};

export function getTargetRelationLine(
  action: MeetingAction | undefined,
  targetId: string | undefined,
  agentList: AgentConfig[],
): string | undefined {
  if (!targetId || !action) return undefined;
  const verb = TARGET_VERB[action];
  if (!verb) return undefined;
  const targetName = agentList.find((a) => a.id === targetId)?.name;
  if (!targetName) return undefined;
  return `${verb} ${targetName}`;
}

export type EmotionBubbleStyle = {
  panel: string;
  tail: string;
  motion?: "shake" | "bounce" | "none";
};

export const EMOTION_BUBBLE_STYLES: Record<Emotion, EmotionBubbleStyle> = {
  angry: {
    panel: "border-rose-200/90 bg-rose-50/95 text-rose-950 shadow-rose-200/50",
    tail: "border-rose-200/90 bg-rose-50/95",
    motion: "shake",
  },
  worried: {
    panel: "border-amber-200/90 bg-amber-50/95 text-amber-950 shadow-amber-200/40",
    tail: "border-amber-200/90 bg-amber-50/95",
    motion: "none",
  },
  excited: {
    panel: "border-orange-200/90 bg-orange-50/95 text-orange-950 shadow-orange-200/45",
    tail: "border-orange-200/90 bg-orange-50/95",
    motion: "bounce",
  },
  thinking: {
    panel: "border-violet-200/90 bg-violet-50/95 text-violet-950 shadow-violet-200/40",
    tail: "border-violet-200/90 bg-violet-50/95",
    motion: "none",
  },
  happy: {
    panel: "border-emerald-200/90 bg-emerald-50/95 text-emerald-950 shadow-emerald-200/40",
    tail: "border-emerald-200/90 bg-emerald-50/95",
    motion: "none",
  },
  neutral: {
    panel: "border-white/80 bg-white/95 text-slate-800 shadow-violet-200/40",
    tail: "border-white/80 bg-white/95",
    motion: "none",
  },
};
