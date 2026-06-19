# Streaming Protocol

## Overview

The chat endpoint (`POST /api/chat`) returns Server-Sent Events (SSE) that stream the agent's response in real-time. The approval endpoint (`POST /api/chat/sessions/{id}/approve`) uses the same protocol for the agent's continuation after approval.

## SSE Event Types

### `text` - Streaming text content

Emitted as the LLM generates text. Multiple events arrive to form the full response.

```
event: text
data: {"type": "text", "content": "The total outstanding"}

event: text
data: {"type": "text", "content": " rent is $15,400.00."}
```

### `tool_start` - Tool execution begins

Emitted when the agent invokes a tool. The frontend can show a loading indicator.

```
event: tool_start
data: {"type": "tool_start", "tool": "execute_readonly_query", "input": {"sql": "SELECT ..."}}
```

### `tool_end` - Tool execution completes

Emitted when a tool finishes. The frontend can dismiss the loading indicator.

```
event: tool_end
data: {"type": "tool_end", "tool": "execute_readonly_query"}
```

### `approval_required` - Action needs user approval

Emitted when the agent tries to execute a write tool. The agent pauses and returns control to the user.

```
event: approval_required
data: {
  "type": "approval_required",
  "interrupt_id": "abc-123-def",
  "action": "send_message",
  "params": {"tenant_id": 5, "body": "Your rent reminder..."},
  "preview": "Send message to tenant #5: \"Your rent reminder...\"",
  "session_id": "sess-xyz"
}
```

### `done` - Stream complete

Final event indicating the stream has ended.

```
event: done
data: {"type": "done", "session_id": "sess-xyz", "stop_reason": "end_turn"}
```

### `error` - Error occurred

Emitted if something goes wrong during processing.

```
event: error
data: {"type": "error", "message": "Database connection failed"}
```

## Approval Flow

1. Client sends `POST /api/chat` with the user's message
2. Agent streams text + tool events
3. If the agent calls a write tool, `approval_required` is emitted and the stream pauses
4. Client displays the approval UI
5. User clicks Approve / Reject / Edit
6. Client sends `POST /api/chat/sessions/{id}/approve` with the decision
7. Agent resumes and streams the continuation (same event types)

## Client Consumption

Since the chat uses POST (not GET), the browser's native `EventSource` API cannot be used. Instead, the frontend uses `fetch()` with `ReadableStream` to parse SSE manually:

```typescript
const res = await fetch('/api/chat', { method: 'POST', body: ... })
const reader = res.body.getReader()
// Parse SSE text protocol line by line
```

## Headers

Responses include anti-buffering headers:

```
Content-Type: text/event-stream
Cache-Control: no-cache, no-store, no-transform
Connection: keep-alive
X-Accel-Buffering: no
```
