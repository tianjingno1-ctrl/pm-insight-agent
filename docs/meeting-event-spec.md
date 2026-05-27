# Meeting Event Spec

This document defines the event protocol for the pony-style AI roundtable UI.

The frontend mock events and future backend SSE events must follow the same structure.

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

## MeetingEvent

```ts
type MeetingEvent = {
  id: string;
  type: "speech" | "reaction" | "summary";

  speakerId?: AgentId;
  targetId?: AgentId;

  emotion?: Emotion;
  action?: MeetingAction;

  text?: string;

  duration_ms?: number;
  delay_before_ms?: number;

  summary?: {
    direction: string;
    disagreement: string;
    nextStep: string;
  };
};
```

## Playback Rules

1. `delay_before_ms` controls the pause before this event starts.
2. `duration_ms` controls how long this event stays active.
3. Only one `speech` event is active in the first mock version.
4. `summary` events should show the final decision card.
5. Future SSE backend must emit compatible `MeetingEvent` objects.

## MVP Constraints

1. First version does not require token-by-token typing.
2. Speech bubble may appear as full text with spring animation.
3. Frontend playback logic must be isolated in `useMeetingPlayer(events)`.
4. UI components should not contain scattered timeout logic.
