"""Simple tests for Codex routing"""
from anthropic_router import create_client
from codex_client import CodexClient


def test_codex_detection():
    client = create_client(provider="codex", api_key="999999999")
    assert isinstance(client.client, CodexClient)
