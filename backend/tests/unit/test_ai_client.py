from unittest.mock import patch, MagicMock

import pytest
import requests

from app.services.ai.ai_client import (
    StubAIClient,
    OllamaAIClient,
    build_ai_client,
)


# --- StubAIClient -----------------------------------------------------

def test_stub_client_response_is_clearly_labeled():
    client = StubAIClient()
    result = client.complete("Improve this job description")
    assert result["text"].startswith("[STUB AI RESPONSE")
    assert "input_tokens" in result
    assert "output_tokens" in result


def test_stub_client_never_makes_a_network_call():
    with patch("requests.post", side_effect=AssertionError("stub must not call requests.post")):
        client = StubAIClient()
        result = client.complete("anything")
    assert result["text"].startswith("[STUB AI RESPONSE")


def _mock_ollama_response(text="Improved description text", prompt_tokens=42, output_tokens=17):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": text,
        "prompt_eval_count": prompt_tokens,
        "eval_count": output_tokens,
    }
    mock_response.raise_for_status.return_value = None
    return mock_response


def test_ollama_client_calls_generate_endpoint_with_expected_payload():
    client = OllamaAIClient(base_url="http://localhost:11434", model="llama3.1:8b")

    with patch("requests.post", return_value=_mock_ollama_response()) as mock_post:
        result = client.complete("Improve this job description", max_tokens=500)

    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "http://localhost:11434/api/generate"
    assert call_args[1]["json"]["model"] == "llama3.1:8b"
    assert call_args[1]["json"]["prompt"] == "Improve this job description"
    assert call_args[1]["json"]["stream"] is False
    assert call_args[1]["json"]["options"]["num_predict"] == 500

    assert result["text"] == "Improved description text"
    assert result["input_tokens"] == 42
    assert result["output_tokens"] == 17


def test_ollama_client_strips_trailing_slash_from_base_url():
    client = OllamaAIClient(base_url="http://localhost:11434/", model="llama3.1:8b")
    with patch("requests.post", return_value=_mock_ollama_response()) as mock_post:
        client.complete("test")
    assert mock_post.call_args[0][0] == "http://localhost:11434/api/generate"


def test_ollama_client_raises_clear_error_when_server_unreachable():
    client = OllamaAIClient(base_url="http://localhost:11434", model="llama3.1:8b")

    with patch("requests.post", side_effect=requests.exceptions.ConnectionError()):
        with pytest.raises(RuntimeError, match="Could not reach Ollama"):
            client.complete("test prompt")


def test_ollama_client_raises_clear_error_on_timeout():
    client = OllamaAIClient(base_url="http://localhost:11434", model="llama3.1:8b", timeout_seconds=5)

    with patch("requests.post", side_effect=requests.exceptions.Timeout()):
        with pytest.raises(RuntimeError, match="did not respond within 5s"):
            client.complete("test prompt")


def test_ollama_client_raises_clear_error_when_model_not_pulled():
    mock_response = MagicMock()
    mock_response.status_code = 404

    client = OllamaAIClient(base_url="http://localhost:11434", model="llama3.1:8b")
    with patch("requests.post", return_value=mock_response):
        with pytest.raises(RuntimeError, match="ollama pull llama3.1:8b"):
            client.complete("test prompt")


def test_ollama_client_propagates_other_http_errors():
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("server error")

    client = OllamaAIClient(base_url="http://localhost:11434", model="llama3.1:8b")
    with patch("requests.post", return_value=mock_response):
        with pytest.raises(requests.exceptions.HTTPError):
            client.complete("test prompt")


# --- build_ai_client -----------------------------------------------------

def test_build_ai_client_defaults_to_stub():
    client = build_ai_client({"AI_PROVIDER": "stub"})
    assert isinstance(client, StubAIClient)


def test_build_ai_client_builds_ollama_client_with_configured_url_and_model():
    client = build_ai_client({
        "AI_PROVIDER": "ollama",
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "llama3.1:8b",
    })
    assert isinstance(client, OllamaAIClient)
    assert client.base_url == "http://localhost:11434"
    assert client.model == "llama3.1:8b"


def test_build_ai_client_ollama_uses_defaults_when_not_configured():
    client = build_ai_client({"AI_PROVIDER": "ollama"})
    assert isinstance(client, OllamaAIClient)
    assert client.base_url == "http://localhost:11434"
    assert client.model == "llama3.1:8b"


def test_build_ai_client_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unknown AI_PROVIDER"):
        build_ai_client({"AI_PROVIDER": "made-up-provider"})


def test_build_ai_client_rejects_anthropic_and_openai_and_gemini():

    for provider in ("anthropic", "openai", "gemini"):
        with pytest.raises(ValueError, match="Unknown AI_PROVIDER"):
            build_ai_client({"AI_PROVIDER": provider})
