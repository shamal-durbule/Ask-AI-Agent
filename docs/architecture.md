# Architecture

## Overview

The Ask AI Agent is a conversational AI backend (with a React frontend) for property management. It uses the Strands Agents SDK to power a chat assistant that can answer data questions and take actions with human approval.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  React Frontend (Vite + TypeScript + Tailwind)                  │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐ ┌───────────────┐   │
│  │ Chat UI  │ │ Sidebar  │ │ Properties │ │    Tenants    │   │
│  │ (SSE)    │ │ Sessions │ │   Page     │ │     Page      │   │
│  └──────────┘ └──────────┘ └────────────┘ └───────────────┘   │
└───────────────────────┬─────────────────────────────────────────┘
                        │ HTTP / SSE
┌───────────────────────▼─────────────────────────────────────────┐
│  FastAPI API Layer (thin routes)                                 │
│  POST /api/chat          GET /api/properties                     │
│  POST /api/chat/sessions/{id}/approve    GET /api/tenants        │
│  GET /api/chat/sessions  GET /api/chat/sessions/{id}/messages    │
└───────────────────────┬─────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────┐
│  Service Layer                                                   │
│  ┌─────────────────┐  ┌─────────────────┐ ┌──────────────────┐ │
│  │  ChatService     │  │ PropertyService │ │  TenantService   │ │
│  │  (orchestrates   │  │  (CRUD)         │ │  (CRUD)          │ │
│  │   agent, SSE,    │  └─────────────────┘ └──────────────────┘ │
│  │   approvals)     │                                            │
│  └────────┬─────────┘                                            │
└───────────┼──────────────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────────────┐
│  Strands Agent                                                    │
│  ┌──────────────┐  ┌──────────────────┐  ┌────────────────────┐ │
│  │  Read Tools   │  │  Analytics Tools │  │   Write Tools      │ │
│  │  (auto)       │  │  (auto, SQL      │  │   (approval-gated) │ │
│  │               │  │   validated)     │  │                    │ │
│  └──────────────┘  └──────────────────┘  └────────┬───────────┘ │
│                                                    │              │
│  ┌──────────────────────┐  ┌──────────────────────▼───────────┐ │
│  │  Analytics Skill      │  │  ApprovalHook                    │ │
│  │  (SKILL.md)           │  │  (BeforeToolCallEvent interrupt) │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
└───────────┬──────────────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────────────┐
│  Repository Layer (data access)                                   │
│  PropertyRepo | TenantRepo | LeaseRepo | ChargeRepo               │
│  MessageRepo  | ChatRepo   | AnalyticsRepo                       │
└───────────┬──────────────────────────────────────────────────────┘
            │
┌───────────▼──────────────────────────────────────────────────────┐
│  PostgreSQL (SQLAlchemy 2.0 async + Alembic)                      │
│  property | unit | tenant | lease | charge | payment              │
│  message | scheduled_message | chat_session | chat_message        │
│  action_log                                                       │
└──────────────────────────────────────────────────────────────────┘
```

## Layering Rules

1. **Routes** call **Services**. No business logic in routes.
2. **Services** call **Repositories**. No raw SQL outside repos.
3. **Repositories** talk to the **database**. Pure data access.
4. **Agent tools** use repositories directly (they are service-level code executed by the agent).
5. No layer skips -- routes don't access the DB directly, tools don't format HTTP responses.

## Key Design Patterns

- **Generic Repository**: `BaseRepository[T]` provides type-safe CRUD; domain repos extend it.
- **Eager Loading**: All list queries use `selectinload()` or `joinedload()` to prevent N+1.
- **Indexed Queries**: Composite indexes on frequently filtered columns.
- **Domain Enums**: Python enums mapped to string columns (not native PG enums for portability).
- **Pydantic DTOs**: Strict input validation on API requests; typed response models.

## Agent Architecture

The Strands Agent uses:
- **AnthropicModel** (Claude Sonnet) with temperature 0.3 for reliability
- **FileSessionManager** for conversation persistence across requests
- **AgentSkills plugin** with the analytics skill for text-to-SQL
- **ApprovalHook** (HookProvider) that intercepts write tools via `BeforeToolCallEvent`

## Single Workspace

This implementation uses a single workspace. All data belongs to one property management company. Multi-tenancy would require scoping every query with a `workspace_id` filter, which is noted as a future enhancement.
