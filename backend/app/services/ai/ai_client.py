
import requests


class BaseAIClient:
    def complete(self, prompt: str, max_tokens: int = 1000) -> dict:
        raise NotImplementedError


class OllamaAIClient(BaseAIClient):

    def __init__(self, base_url: str, model: str, timeout_seconds: int = 60):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def complete(self, prompt: str, max_tokens: int = 1000) -> dict:
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": max_tokens},
                },
                timeout=self.timeout_seconds,
            )
        except requests.exceptions.ConnectionError as exc:
            raise RuntimeError(
                f"Could not reach Ollama at {self.base_url} — is `ollama serve` running? "
                f"(AI_PROVIDER=ollama requires a local Ollama server; set AI_PROVIDER=stub "
                f"to disable AI calls entirely.)"
            ) from exc
        except requests.exceptions.Timeout as exc:
            raise RuntimeError(
                f"Ollama at {self.base_url} did not respond within {self.timeout_seconds}s. "
                f"The model '{self.model}' may still be loading — try again, or check "
                f"`ollama list` to confirm it's pulled."
            ) from exc

        if response.status_code == 404:
            raise RuntimeError(
                f"Ollama model '{self.model}' was not found at {self.base_url}. "
                f"Pull it first: `ollama pull {self.model}`."
            )
        response.raise_for_status()

        body = response.json()
        return {
            "text": body.get("response", ""),
            "input_tokens": body.get("prompt_eval_count"),
            "output_tokens": body.get("eval_count"),
        }


class StubAIClient(BaseAIClient):

    def complete(self, prompt: str, max_tokens: int = 1000) -> dict:
        return {
            "text": f"[STUB AI RESPONSE — AI_PROVIDER=stub, no model called] {prompt[:200]}",
            "input_tokens": len(prompt) // 4,
            "output_tokens": 20,
        }


def build_ai_client(config) -> BaseAIClient:
    provider = config.get("AI_PROVIDER", "stub")
    if provider == "ollama":
        return OllamaAIClient(
            base_url=config.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            model=config.get("OLLAMA_MODEL", "llama3.1:8b"),
        )
    if provider == "stub":
        return StubAIClient()
    raise ValueError(f"Unknown AI_PROVIDER: {provider}")
