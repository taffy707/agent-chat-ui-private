# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Agent Chat UI is a Next.js application that provides a chat interface for interacting with any LangGraph server that has a `messages` key. It uses the LangGraph SDK to stream responses and manage conversation state.

## Development Commands

```bash
# Install dependencies
pnpm install

# Run development server (starts on http://localhost:3000)
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start

# Lint code
pnpm lint

# Lint and auto-fix
pnpm lint:fix

# Format code with Prettier
pnpm format

# Check formatting
pnpm format:check
```

## Environment Configuration

Copy `.env.example` to `.env` and configure:

- `NEXT_PUBLIC_API_URL`: LangGraph server URL (defaults to `http://localhost:2024`)
- `NEXT_PUBLIC_ASSISTANT_ID`: Graph or assistant ID (defaults to `agent`)
- `LANGSMITH_API_KEY`: For production deployments (not needed for local dev, do NOT prefix with `NEXT_PUBLIC_`)
- `LANGGRAPH_API_URL`: Production LangGraph server URL (used by API passthrough)

**Important**: The `NEXT_PUBLIC_` prefix exposes variables to the client. Only use it for non-sensitive configuration.

## Architecture

### Provider Hierarchy

The app uses a nested provider structure (from [page.tsx](src/app/page.tsx)):

```
ThreadProvider → StreamProvider → ArtifactProvider → Thread Component
```

- **ThreadProvider** ([Thread.tsx](src/providers/Thread.tsx)): Manages thread list and thread metadata using the LangGraph SDK client
- **StreamProvider** ([Stream.tsx](src/providers/Stream.tsx)): Core streaming functionality using `useStream` from `@langchain/langgraph-sdk/react`. Handles real-time message streaming, UI messages, and connection state
- **ArtifactProvider** ([artifact.tsx](src/components/thread/artifact.tsx)): Manages artifact rendering in a side panel using React Portals

### Key Concepts

**State Type**: The application expects LangGraph servers to return state with this shape:
```typescript
{ messages: Message[]; ui?: UIMessage[] }
```

**Message Filtering**: Messages with IDs prefixed with `do-not-render-` (defined in [ensure-tool-responses.ts](src/lib/ensure-tool-responses.ts)) are hidden from the UI. This is useful for internal tool calls that shouldn't be displayed.

**UI Messages**: Custom UI components can be sent via the `ui` state key and streamed through custom events. The reducer is defined in `@langchain/langgraph-sdk/react-ui`.

**Interrupts**: The app supports LangGraph interrupts using the "agent inbox" pattern ([agent-inbox-interrupt.ts](src/lib/agent-inbox-interrupt.ts)). This allows graphs to request human feedback with configurable actions (respond, accept, edit, ignore).

### API Passthrough

For production deployments, the app includes an API passthrough ([api/[..._path]/route.ts](src/app/api/[..._path]/route.ts)) using `langgraph-nextjs-api-passthrough`. This proxies requests to your LangGraph server and injects the `LANGSMITH_API_KEY` server-side, preventing exposure of API keys to clients.

### Component Structure

- **src/components/thread/**: Main chat interface components
  - [index.tsx](src/components/thread/index.tsx): Core Thread component with message rendering
  - **messages/**: Message type renderers (ai.tsx, human.tsx, tool-calls.tsx, generic-interrupt.tsx)
  - **agent-inbox/**: Interrupt handling UI for human-in-the-loop workflows
  - [artifact.tsx](src/components/thread/artifact.tsx): Artifact rendering system using React Portals
  - [history/](src/components/thread/history/): Thread history sidebar
- **src/components/ui/**: Reusable UI components (shadcn/ui based)
- **src/lib/**: Utility functions and type definitions

### State Management

State is managed through React Context and URL query parameters (using `nuqs`):
- `threadId`: Current conversation thread
- `apiUrl`: LangGraph server endpoint
- `assistantId`: Graph/assistant identifier

The LangGraph SDK client ([client.ts](src/providers/client.ts)) handles all API communication.

## Message Visibility Control

Two mechanisms control message visibility:

1. **Prevent streaming**: Add `langsmith:nostream` tag to the chat model config
2. **Hide permanently**: Prefix message ID with `do-not-render-` and add `langsmith:do-not-render` tag

See README for implementation examples.

## Artifacts

Artifacts are rendered in a side panel. Access via `useArtifact` hook from `thread.meta.artifact`. The Artifact component renders content using React Portals into designated slots.

## TypeScript Configuration

Path alias `@/*` maps to `src/*` for cleaner imports.
