# Meeting Event Spec

This document defines the event protocol for the pony-style AI roundtable UI.

The frontend mock events and future backend SSE events **must follow the same structure**.

**Protocol version default**: if `protocolVersion` is omitted, treat it as `"1.0"`.

**Compatibility**: all fields listed under `MeetingEvent` except `id` and `type` are **optional**. Existing mock payloads that only use `speech` and `summary` remain valid without modification.

---

## AgentId

```ts
type AgentId = "host" | "product" | "tech" | "growth";
```

## Emotion

```ts
type Emotion =
  | "neutral"
  | "happy"
  | "thinking"
  | "worried"
  | "angry"
  | "excited";
```

## MeetingAction

```ts
type MeetingAction =
  | "open"
  | "suggest"
  | "challenge"
  | "support"
  | "reject"
  | "summarize";
```

## MeetingStage

```ts
type MeetingStage =
  | "opening"
  | "proposal"
  | "challenge"
  | "synthesis"
  | "closing";
```

## UiHint

```ts
type UiHint = {
  bubbleVariant?: "normal" | "warning" | "challenge" | "success";
  motion?: "pop" | "shake" | "bounce" | "glow";
  sound?: "none" | "pop" | "tap";
};
```

## ErrorInfo

```ts
type ErrorInfo = {
  code: string;
  message: string;
  recoverable: boolean;
};
```

## MeetingSummary

```ts
type MeetingSummary = {
  direction: string;
  disagreement: string;
  nextStep: string;
};
```

## MeetingEvent

```ts
type MeetingEventType =
  | "meeting_started"
  | "speech"
  | "reaction"      // reserved / optional — see Phase 2.1 subset
  | "summary"
  | "meeting_done"
  | "error";

type MeetingEvent = {
  id: string;
  type: MeetingEventType;

  // Role / content (optional depending on type)
  speakerId?: AgentId;
  targetId?: AgentId;
  emotion?: Emotion;
  action?: MeetingAction;
  text?: string;

  // Timing (optional; see Playback Rules)
  duration_ms?: number;
  delay_before_ms?: number;

  // Summary payload (typically type === "summary")
  summary?: MeetingSummary;

  // --- All fields below are optional extensions (v1.0+) ---

  stage?: MeetingStage;
  intensity?: 1 | 2 | 3 | 4 | 5;
  turnIndex?: number;
  roundIndex?: number;
  protocolVersion?: string; // default "1.0" when absent

  uiHint?: UiHint;

  errorInfo?: ErrorInfo;
};
```

### Optional fields policy

| Rule | Detail |
|------|--------|
| Mock today | `frontend/lib/mockEvents.ts` **does not need** to emit new optional fields immediately. |
| Default version | Missing `protocolVersion` → interpret as `"1.0"`. |
| SSE backend | Future FastAPI/SSE **must** emit objects compatible with this spec; may add optional fields but must not break consumers that ignore unknown keys. |
| Unknown fields | Clients should ignore unknown top-level keys (forward compatibility). |

---

## Event type semantics

| `type` | Purpose | Typical `speakerId` | Visual default |
|--------|---------|---------------------|----------------|
| `meeting_started` | Session / round begins, venue ready | Usually omitted | **Non-visual** (no role bubble) |
| `speech` | Spoken line with full text | Required for bubble UX | Role bubble + avatar state |
| `reaction` | Short non-verbal beat (reserved) | Optional | **Reserved** — Phase 2.1 may skip |
| `summary` | Final decision card | Usually omitted | `SummaryCard` (not a speech bubble) |
| `meeting_done` | Session / round complete | Usually omitted | **Non-visual** (no role bubble) |
| `error` | Failure or recoverable fault | Usually omitted | Error banner / toast (must not crash UI) |

---

## Control event playback rules

These rules apply to **`meeting_started`**, **`meeting_done`**, and **`error`** (control / lifecycle events).

### `meeting_started` / `meeting_done`

1. **Do not** render as a character speech bubble by default (no `speakerId` → no “air bubble”).
2. **Default** `duration_ms = 0` when omitted (advance immediately after `delay_before_ms`).
3. May drive **top status bar**, “会场初始化”, or “会议已结束” states via `uiHint` or app-level state — not `PonyAgent` bubbles.
4. Hook implementations **must not** leave the timeline idle for a long `duration_ms` with no visible UI (avoid “timeline spinning in empty air”).

### `error`

1. May appear **at any point** in the stream (including mid-meeting).
2. UI should show a **clear, non-blocking error message** (`errorInfo.message`); must **not** throw or white-screen.
3. If `errorInfo.recoverable === true`, UI may offer retry / continue; otherwise pause playback.
4. Default: **non-bubble**; do not require `speakerId`.

### `reaction` (reserved)

1. Listed in the protocol for forward compatibility.
2. **Phase 2.1 does not require** mock or UI support.
3. If implemented later: short duration, optional `emotion` / `uiHint.motion`, may omit `text`.

---

## Playback rules (all types)

1. `delay_before_ms` — pause before this event becomes active (default implementation: 300ms if omitted).
2. `duration_ms` — how long the event stays active before advancing (see per-type defaults below).
3. **One primary “speech” bubble** at a time in the first mock player (`type === "speech"` with `speakerId`).
4. `summary` — show final decision card; ends or pauses main speech timeline per player policy.
5. Future SSE backends emit **ordered** `MeetingEvent` JSON lines or SSE `data:` frames; same shape as mock array items.

### Recommended defaults (when fields omitted)

| `type` | `duration_ms` default | Notes |
|--------|----------------------|--------|
| `meeting_started` | `0` | Control only |
| `speech` | `2500` | Full bubble visible |
| `reaction` | `800` | If implemented |
| `summary` | until dismissed or `0` + hold card | Player may stop `isPlaying` |
| `meeting_done` | `0` | Control only |
| `error` | `0` or hold until ack | Show until user dismisses if non-recoverable |

---

## Phase 2.1 implementation subset

What the **current frontend** must support vs. what is **deferred**:

| Capability | Phase 2.1 | Notes |
|------------|-----------|--------|
| `speech` | **Required** | Existing mock + bubble UX |
| `summary` | **Required** | Existing `SummaryCard` |
| `reaction` | **Optional** | Protocol reserved; mock may omit |
| `meeting_started` | **Deferred UI** | Spec + hook must not break; no full status UI required yet |
| `meeting_done` | **Deferred UI** | Same as above |
| `error` | **Deferred UI** | Spec only; hook must handle without crash / timeline stall |
| Optional metadata (`stage`, `intensity`, `turnIndex`, …) | **Ignored OK** | UI may read later in 2.1b |

### Hook layer requirement (Phase 2.1a, code — documented here only)

When `meeting_started` / `meeting_done` / `error` appear in the event list, `useMeetingPlayer` (and future `useMeetingPlayerFromSSE`) **must**:

- Advance the timeline without assuming every event is `speech`.
- Not set `currentEvent` to a bubble-visible state for non-visual control events unless explicitly designed.
- Treat unknown or control types with **`duration_ms` default `0`** unless specified.

---

## MVP constraints (unchanged)

1. No token-by-token typing required in Phase 2.1.
2. Speech bubble may show **full text** with spring animation.
3. Playback logic stays in **`useMeetingPlayer`** (or SSE variant) — **no scattered `setTimeout` in UI components**.
4. `frontend/lib/types.ts` should mirror this document when updated in Phase 2.1a (code change, not part of Batch A).

---

## SSE backend requirements (Phase 2.2+)

1. Emit `MeetingEvent` objects matching this spec (JSON).
2. Set `protocolVersion: "1.0"` (or higher when negotiated).
3. Prefer explicit `meeting_started` before first `speech` and `meeting_done` after final `summary` or last `speech`.
4. On failure, emit `error` with populated `errorInfo`; do not send malformed partial blobs.
5. Same field names and enum values as mock — **no parallel ad-hoc schema**.

---

*Spec revision: Batch A contract docs · aligns with experiment branch Phase 2.1 planning*
