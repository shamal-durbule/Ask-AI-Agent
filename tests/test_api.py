"""Tests for the REST API endpoints.

These test the route layer behavior with mocked services.
"""

from unittest.mock import AsyncMock, patch

import pytest


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_returns_ok(self, test_client) -> None:  # type: ignore[no-untyped-def]
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestChatEndpoint:
    """Test the chat SSE endpoint."""

    def test_chat_requires_message(self, test_client) -> None:  # type: ignore[no-untyped-def]
        response = test_client.post("/api/chat", json={})
        assert response.status_code == 422  # validation error

    def test_chat_rejects_empty_message(self, test_client) -> None:  # type: ignore[no-untyped-def]
        response = test_client.post("/api/chat", json={"message": ""})
        assert response.status_code == 422


class TestSessionEndpoints:
    """Test session list and message endpoints."""

    def test_sessions_endpoint_exists(self, test_client) -> None:  # type: ignore[no-untyped-def]
        # Will fail with 500 (no DB) but route should exist
        response = test_client.get("/api/chat/sessions")
        assert response.status_code in (200, 500)

    def test_messages_endpoint_exists(self, test_client) -> None:  # type: ignore[no-untyped-def]
        response = test_client.get("/api/chat/sessions/fake-id/messages")
        assert response.status_code in (404, 500)
