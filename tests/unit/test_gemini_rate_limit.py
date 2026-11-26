import pytest

from services import gemini


class FakeLLM:
    calls = 0

    def invoke(self, prompt):
        self.calls += 1
        return "ok"


@pytest.fixture
def clock(monkeypatch):
    now = [1000.0]
    monkeypatch.setattr(gemini.time, "monotonic", lambda: now[0])
    monkeypatch.setattr(gemini.settings, "gemini_rpm", 2)
    gemini._recent_calls.clear()
    yield now
    gemini._recent_calls.clear()


def test_calls_over_the_limit_are_refused_without_reaching_gemini(clock):
    llm = FakeLLM()
    gemini.invoke_with_retry(llm, "a")
    gemini.invoke_with_retry(llm, "b")

    with pytest.raises(gemini.GeminiError, match="rate limit"):
        gemini.invoke_with_retry(llm, "c")
    assert llm.calls == 2


def test_calls_are_allowed_again_after_a_minute(clock):
    llm = FakeLLM()
    gemini.invoke_with_retry(llm, "a")
    gemini.invoke_with_retry(llm, "b")
    clock[0] += 60

    assert gemini.invoke_with_retry(llm, "c") == "ok"
