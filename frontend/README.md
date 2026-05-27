This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Meeting event source (Phase 2.2)

Default: **mock** (`mockEvents.ts`) — no backend required.

Optional SSE (requires [backend](../backend/README.md) on port 8000):

```powershell
$env:NEXT_PUBLIC_MEETING_SOURCE="sse"
$env:NEXT_PUBLIC_MEETING_SCENARIO="default"   # optional
$env:NEXT_PUBLIC_MEETING_PACE="1.0"            # optional
$env:NEXT_PUBLIC_MEETING_SSE_URL="http://127.0.0.1:8000/api/meetings/mock-stream"  # optional
npm run dev
```

| Variable | Default |
|----------|---------|
| `NEXT_PUBLIC_MEETING_SOURCE` | `mock` |
| `NEXT_PUBLIC_MEETING_SSE_URL` | `http://127.0.0.1:8000/api/meetings/mock-stream` |
| `NEXT_PUBLIC_MEETING_SCENARIO` | `default` |
| `NEXT_PUBLIC_MEETING_PACE` | `1.0` |
| `NEXT_PUBLIC_MEETING_TOPIC` | *(empty — omit from URL)* |

SSE mode buffers the full stream (`meeting_done`) before playback starts.

### Demo LLM (Phase 2.3-Demo)

Requires backend with optional `OPENAI_API_KEY` (falls back to local script if missing).

```powershell
$env:NEXT_PUBLIC_MEETING_SOURCE="sse"
$env:NEXT_PUBLIC_MEETING_SCENARIO="llm"
$env:NEXT_PUBLIC_MEETING_TOPIC="AI会不会取代产品经理"
$env:NEXT_PUBLIC_MEETING_PACE="4.0"
npm run dev
```

- Full script is generated first, then played as `MeetingEvent` over SSE (not token streaming).
- Restart `npm run dev` after changing `NEXT_PUBLIC_*`.
- Default **mock** mode still needs no backend.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
