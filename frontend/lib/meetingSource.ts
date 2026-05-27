export type MeetingSource = "mock" | "sse";

const DEFAULT_SSE_URL = "http://127.0.0.1:8000/api/meetings/mock-stream";

export function getMeetingSource(): MeetingSource {
  return process.env.NEXT_PUBLIC_MEETING_SOURCE === "sse" ? "sse" : "mock";
}

export function getMeetingSseUrl(): string {
  return process.env.NEXT_PUBLIC_MEETING_SSE_URL ?? DEFAULT_SSE_URL;
}

export function getMeetingScenario(): string {
  return process.env.NEXT_PUBLIC_MEETING_SCENARIO ?? "default";
}

export function getMeetingPace(): number {
  const raw = process.env.NEXT_PUBLIC_MEETING_PACE;
  if (raw === undefined || raw === "") {
    return 1.0;
  }
  const pace = Number(raw);
  return Number.isFinite(pace) ? pace : 1.0;
}

export function getMeetingTopic(): string | undefined {
  const raw = process.env.NEXT_PUBLIC_MEETING_TOPIC;
  if (raw === undefined) {
    return undefined;
  }
  const trimmed = raw.trim();
  return trimmed.length > 0 ? trimmed : undefined;
}

/** Resolved at build time (Next.js `NEXT_PUBLIC_*`). */
export const meetingSource = getMeetingSource();
