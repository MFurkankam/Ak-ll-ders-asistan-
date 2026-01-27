import os

import pytest

from utils.groq_client import GroqClient


class _FakeResult:
    def __init__(self, content):
        self.content = content


class _FakeChain:
    def __init__(self, content):
        self._content = content

    def invoke(self, _inputs):
        return _FakeResult(self._content)


class _FakePrompt:
    def __init__(self, content):
        self._content = content

    def __or__(self, _llm):
        return _FakeChain(self._content)


class _FakeCompletions:
    @staticmethod
    def create(**_kwargs):
        class _Msg:
            content = "Mock chat reply"

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()


class _FakeClient:
    chat = type("chat", (), {"completions": _FakeCompletions()})()


def _fake_from_template(_template):
    return _FakePrompt("Mock LLM response")


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError):
        GroqClient(api_key=None)


def test_generate_summary_uses_mock(monkeypatch):
    monkeypatch.setattr("utils.groq_client.PromptTemplate.from_template", _fake_from_template)
    client = GroqClient(api_key="test_key")
    summary = client.generate_summary("context")
    assert summary == "Mock LLM response"


def test_answer_question_uses_mock(monkeypatch):
    monkeypatch.setattr("utils.groq_client.PromptTemplate.from_template", _fake_from_template)
    client = GroqClient(api_key="test_key")
    answer = client.answer_question("question", [])
    assert answer == "Mock LLM response"


def test_chat_uses_mock(monkeypatch):
    client = GroqClient(api_key="test_key")
    monkeypatch.setattr(client, "client", _FakeClient())
    reply = client.chat("hello")
    assert reply == "Mock chat reply"
