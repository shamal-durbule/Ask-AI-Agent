# Design Decisions and Tradeoffs

## 1. Analytics Skill: `SKILL.md` Folded Into the System Prompt

**Decision**: Keep the analytics skill as a `SKILL.md` file (name, description, allowed-tools, and SQL guidance) and load its instruction body into the agent's system prompt at agent-creation time (`factory._build_system_prompt`). The two analytics tools (`get_database_schema`, `execute_readonly_query`) are registered directly on the agent.

**Why**: This keeps the skill authored as a standalone, reviewable document while guaranteeing the guidance is actually in context for every turn. It avoids depending on SDK-version-specific skill-discovery behavior, which keeps the agent deterministic and easy to test.

**Tradeoff**: We forgo true progressive disclosure (loading skill instructions only on demand). For a single, always-relevant analytics skill this is a reasonable cost; the body is small. For many large skills, on-demand loading or the Meta-Tool / isolated sub-agent pattern would provide better context separation and token efficiency.

## 2. FileSessionManager vs PostgreSQL Sessions

**Decision**: Use Strands' built-in `FileSessionManager` for agent conversation state, plus PostgreSQL `chat_session`/`chat_message` tables for the REST API.

**Why**: The `FileSessionManager` handles the complex internal state (tool call results, intermediate reasoning) that the agent needs for continuity. Our PostgreSQL tables store the user-facing message history for listing sessions and viewing history.

**Tradeoff**: Dual storage adds slight complexity. In production, a custom `SessionManager` backed by PostgreSQL or Redis would consolidate this. The file-based approach is simple and works for a single-server deployment.

## 3. Hook-Based vs Tool-Based Approval

**Decision**: Use `ApprovalHook` (HookProvider with `BeforeToolCallEvent`) for the approval gate.

**Why**: Separates the approval concern from tool logic. Write tools are pure functions that execute the action; the hook handles the interrupt flow. This means adding a new write tool only requires adding its name to `WRITE_TOOLS`.

**Tradeoff**: The hook approach is slightly less flexible for tool-specific preview generation. We solve this with the `_build_preview()` function that formats each tool's params differently.

## 4. SQL Validation with sqlglot

**Decision**: Use `sqlglot` to parse and validate generated SQL before execution.

**Why**: `sqlglot` can parse SQL into an AST, letting us verify the statement type (SELECT only), check for forbidden operations in subqueries, and inject LIMIT if missing. It's more robust than regex-based validation.

**Tradeoff**: sqlglot may not support every PostgreSQL dialect feature perfectly. We mitigate this with defense-in-depth at the database level: each analytics query runs in a transaction that is set `READ ONLY` (issued before any other statement) with a `statement_timeout`, and the result set is capped via an injected `LIMIT`. The production-grade hardening would be to run analytics queries through a dedicated least-privilege PostgreSQL role with only `SELECT` granted, so read-only is enforced by the database regardless of the application path.

## 5. Single Workspace

**Decision**: All data belongs to a single workspace. No multi-tenant query scoping.

**Why**: Reduces complexity for a take-home assignment. The auth dependency (`get_workspace_id`, reading the `X-Workspace-Id` header and defaulting to `'default'`) is wired into the REST read endpoints, so every request resolves a workspace id today; adding workspace-scoped queries is then a matter of threading that id into the repositories.

**What I'd do with more time**: Add a `workspace_id` column to all domain tables, add a `workspace_id` parameter to all repository methods, and inject it via the auth middleware dependency.

## 6. Async SQLAlchemy with asyncpg

**Decision**: Use SQLAlchemy 2.0 async mode with `asyncpg` driver.

**Why**: FastAPI is async-native, and the Strands SDK's `stream_async` requires an async context. Using async all the way down prevents blocking the event loop during database operations.

**Tradeoff**: Async SQLAlchemy has some gotchas around lazy loading (must use eager loading or `selectinload`). We handle this by explicitly loading relationships in every query.

## 7. React Frontend (bonus)

**Decision**: Include a React + TypeScript + Tailwind frontend despite the assignment saying "not evaluated."

**Why**: A visual demo is more compelling than curl transcripts. The frontend also validates the streaming protocol design.

**Tradeoff**: Time spent on frontend is time not spent on backend polish. We kept the frontend lean (no state management library, no component library) to minimize this.

## 8. Exactly-Once Execution

**Decision**: Use an `action_log` table with status transitions (`pending -> approved -> executed`) and CAS (Compare-And-Swap) updates.

**Why**: The assignment requires that "an approved action must execute exactly once, even if the request is retried or the process restarts." CAS updates (WHERE status = 'approved') prevent double execution.

**Tradeoff**: This is application-level idempotency, not distributed-system-level. For true distributed exactly-once, you'd need an idempotency key in the request and transactional outbox pattern.

## What I'd Do With More Time

1. **Custom PostgreSQL SessionManager** -- consolidate agent state and chat history in one store
2. **Multi-workspace scoping** -- workspace_id on all tables, enforced in every query
3. **Rate limiting** -- per-user/workspace API rate limits
4. **Observability** -- structured logging, OpenTelemetry tracing through agent calls
5. **More thorough testing** -- integration tests with a real database, end-to-end SSE tests
6. **Streaming tool results** -- use Strands' async generator tools to stream SQL results row-by-row
7. **Context window management** -- implement Strands' ContextWindowManager for long conversations
8. **Guardrails** -- input/output filtering to prevent prompt injection in the analytics skill
