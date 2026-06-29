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
        # Rely on prompt-instructed JSON + defensive parsing: newer models (opus-4-8)
        # reject assistant-prefill, so we cannot force the leading "{" that way.
        sys_prompt = system + ("\n\nReturn ONLY a single JSON object, no prose." if json_mode else "")
        messages = [{"role": "user", "content": user}]
        base = dict(model=model, max_tokens=max_tokens, system=sys_prompt, messages=messages)
        # Newer models (e.g. opus-4-8) deprecate `temperature`; try with it, then without.
        for kwargs in ({**base, "temperature": temperature}, base):
            try:
                msg = client.messages.create(**kwargs)
            except Exception as e:  # noqa: BLE001 - surface any SDK/API failure uniformly
                if "temperature" in str(e).lower() and kwargs is not base:
                    continue
                raise ProviderError(f"anthropic call failed: {e}") from e
            return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")


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
        import os
        import random
        import time

        # Gemini 3.x are *thinking* models. On a large bundle the unbounded thinking pass
        # can run ~150s+; the server then sheds the long request as "503 UNAVAILABLE
        # (high demand)" — a misleading message for what is really a request-duration limit
        # (verified: trivial prompts return in ~1s; only the long full-bundle call 503s, and
        # only when it drifts past ~100s). Two defenses: (1) cap the thinking budget so calls
        # bias toward fast completions; (2) a high client timeout + patient, jittered retry so
        # a slow-but-valid completion isn't cut and transient sheds get another window.
        think_budget = int(os.environ.get("REVIEW_GOOGLE_THINKING_BUDGET", "2048"))
        attempts = int(os.environ.get("REVIEW_GOOGLE_RETRIES", "6"))
        client = genai.Client(
            api_key=key,
            http_options=types.HttpOptions(timeout=600_000),  # ms; don't cut a slow-but-OK call
        )
        cfg_kwargs = dict(
            system_instruction=system,
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json" if json_mode else "text/plain",
        )
        if think_budget >= 0 and hasattr(types, "ThinkingConfig"):
            cfg_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=think_budget)
        cfg = types.GenerateContentConfig(**cfg_kwargs)

        last = None
        for attempt in range(attempts):
            try:
                resp = client.models.generate_content(model=model, contents=user, config=cfg)
            except Exception as e:  # noqa: BLE001
                last = e
                msg = str(e)
                if any(s in msg for s in ("503", "UNAVAILABLE", "500", "overloaded", "429")):
                    # server-side load-shed / deadline: back off (capped, jittered) and retry.
                    if attempt < attempts - 1:
                        time.sleep(min(30.0, 4.0 * (2 ** attempt)) + random.uniform(0, 3))
                    continue
                raise ProviderError(f"google call failed: {e}") from e
            text = resp.text or ""
            if text.strip():
                return text
            # empty text: usually thinking consumed the whole budget (finish_reason MAX_TOKENS)
            fr = None
            for c in (resp.candidates or []):
                fr = getattr(c, "finish_reason", None)
            raise ProviderError(
                f"google returned empty text (finish_reason={fr}); "
                f"raise max_tokens (thinking budget may be exhausting it)")
        raise ProviderError(f"google call failed after {attempts} retries: {last}")


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
