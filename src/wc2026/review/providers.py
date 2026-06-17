"""Model-provider adapters behind one interface.

Each provider turns (system, user) into text. SDKs are imported lazily so the core
project never depends on them and a missing key/SDK degrades to a clear error for *that*
reviewer only. API keys come from the environment, never config or code:

    anthropic -> ANTHROPIC_API_KEY
    openai    -> OPENAI_API_KEY
    google    -> GOOGLE_API_KEY (or GEMINI_API_KEY)

Model ids are passed in (from config / REVIEW_<PROVIDER>_MODEL); providers do not hardcode
them. JSON-output mode is requested natively where the SDK supports it; the orchestrator
also parses defensively, so a provider that ignores the request still works.
"""
from __future__ import annotations

import os
from typing import Protocol


class ProviderError(RuntimeError):
    """Raised when a provider cannot be used (missing key/SDK) or a call fails."""


class Provider(Protocol):
    name: str
    def generate(self, system: str, user: str, *, model: str,
                 max_tokens: int, temperature: float, json_mode: bool = True) -> str: ...


def _require_key(*names: str) -> str:
    for n in names:
        v = os.environ.get(n)
        if v:
            return v
    raise ProviderError(f"set one of {', '.join(names)} in the environment")


class AnthropicProvider:
    name = "anthropic"

    def generate(self, system, user, *, model, max_tokens, temperature, json_mode=True):
        key = _require_key("ANTHROPIC_API_KEY")
        try:
            import anthropic
        except ImportError as e:
            raise ProviderError("pip install anthropic") from e
        client = anthropic.Anthropic(api_key=key)
        messages = [{"role": "user", "content": user}]
        if json_mode:
            # prefill the assistant turn with "{" so the model must emit a JSON object
            messages.append({"role": "assistant", "content": "{"})
        try:
            msg = client.messages.create(
                model=model, max_tokens=max_tokens, temperature=temperature,
                system=system, messages=messages,
            )
        except Exception as e:  # noqa: BLE001 - surface any SDK/API failure uniformly
            raise ProviderError(f"anthropic call failed: {e}") from e
        text = "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")
        return ("{" + text) if json_mode else text


class OpenAIProvider:
    name = "openai"

    def generate(self, system, user, *, model, max_tokens, temperature, json_mode=True):
        key = _require_key("OPENAI_API_KEY")
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ProviderError("pip install openai") from e
        client = OpenAI(api_key=key)
        base = dict(model=model,
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": user}])
        if json_mode:
            base["response_format"] = {"type": "json_object"}
        # Newer reasoning models reject `temperature` and rename max_tokens; try the
        # rich call, then progressively strip unsupported params.
        attempts = [
            {**base, "temperature": temperature, "max_tokens": max_tokens},
            {**base, "max_completion_tokens": max_tokens},
            base,
        ]
        last = None
        for kwargs in attempts:
            try:
                resp = client.chat.completions.create(**kwargs)
                return resp.choices[0].message.content or ""
            except TypeError as e:
                last = e
            except Exception as e:  # noqa: BLE001
                last = e
                if "param" not in str(e).lower() and "unsupported" not in str(e).lower():
                    break
        raise ProviderError(f"openai call failed: {last}")


class GoogleProvider:
    name = "google"

    def generate(self, system, user, *, model, max_tokens, temperature, json_mode=True):
        key = _require_key("GOOGLE_API_KEY", "GEMINI_API_KEY")
        try:
            from google import genai
            from google.genai import types
        except ImportError as e:
            raise ProviderError("pip install google-genai") from e
        client = genai.Client(api_key=key)
        cfg = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json" if json_mode else "text/plain",
        )
        try:
            resp = client.models.generate_content(model=model, contents=user, config=cfg)
        except Exception as e:  # noqa: BLE001
            raise ProviderError(f"google call failed: {e}") from e
        return resp.text or ""


class MockProvider:
    """Offline provider for tests / dry runs: echoes a valid, schema-shaped review."""
    name = "mock"

    def generate(self, system, user, *, model, max_tokens, temperature, json_mode=True):
        import json
        return json.dumps({
            "summary": f"[mock:{model}] dry-run review; no API call made.",
            "scores": {"novelty": 3, "rigor": 3, "significance": 3,
                       "clarity": 3, "reproducibility": 3},
            "major_concerns": [{
                "issue": "mock concern", "why_it_matters": "n/a",
                "evidence_location": "n/a", "suggested_fix": "n/a", "severity": "minor"}],
            "minor_concerns": [], "blind_spots": [], "inconsistencies": [],
            "missing_prior_art": [], "suggested_experiments": [],
            "ai_authorship": {"overall_likelihood": 0.5, "confidence": "low", "tells": []},
            "questions_for_authors": [], "recommendation": "major_revision",
        })


_REGISTRY = {p.name: p for p in (AnthropicProvider(), OpenAIProvider(),
                                 GoogleProvider(), MockProvider())}


def get_provider(name: str) -> Provider:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise ProviderError(f"unknown provider '{name}'; have {sorted(_REGISTRY)}") from None
