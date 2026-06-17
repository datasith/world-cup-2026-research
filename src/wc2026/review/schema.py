"""Structured review schema + defensive parsing.

Kept dependency-free (dataclasses, not pydantic) so the review subsystem adds no hard
deps to the core project. ``REVIEW_JSON_SCHEMA`` is the contract handed to each model
(via native JSON/structured-output modes where available); :func:`parse_review`
tolerantly parses whatever JSON the model returns, since providers differ in how strictly
they honor a schema.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

# JSON Schema given to providers that support structured output (OpenAI json_schema,
# Google response_schema, Anthropic tool input_schema). Intentionally permissive on
# arrays so a model never has to omit a field; we validate softly on parse.
REVIEW_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "scores": {
            "type": "object",
            "properties": {
                "novelty": {"type": "integer"},
                "rigor": {"type": "integer"},
                "significance": {"type": "integer"},
                "clarity": {"type": "integer"},
                "reproducibility": {"type": "integer"},
            },
            "required": ["novelty", "rigor", "significance", "clarity", "reproducibility"],
        },
        "major_concerns": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "issue": {"type": "string"},
                "why_it_matters": {"type": "string"},
                "evidence_location": {"type": "string"},
                "suggested_fix": {"type": "string"},
                "severity": {"type": "string", "enum": ["critical", "major", "minor"]},
            },
            "required": ["issue", "why_it_matters", "evidence_location", "suggested_fix", "severity"],
        }},
        "minor_concerns": {"type": "array", "items": {"type": "string"}},
        "blind_spots": {"type": "array", "items": {"type": "string"}},
        "inconsistencies": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "claim_a": {"type": "string"},
                "claim_b": {"type": "string"},
                "location": {"type": "string"},
                "explanation": {"type": "string"},
            },
            "required": ["claim_a", "claim_b", "location", "explanation"],
        }},
        "missing_prior_art": {"type": "array", "items": {"type": "string"}},
        "suggested_experiments": {"type": "array", "items": {"type": "string"}},
        "ai_authorship": {
            "type": "object",
            "properties": {
                "overall_likelihood": {"type": "number"},
                "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                "tells": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "quote": {"type": "string"},
                        "location": {"type": "string"},
                        "why_ai_sounding": {"type": "string"},
                        "suggested_human_revision": {"type": "string"},
                    },
                    "required": ["quote", "location", "why_ai_sounding", "suggested_human_revision"],
                }},
            },
            "required": ["overall_likelihood", "confidence", "tells"],
        },
        "questions_for_authors": {"type": "array", "items": {"type": "string"}},
        "recommendation": {"type": "string",
                           "enum": ["reject", "major_revision", "minor_revision", "accept"]},
    },
    "required": ["summary", "scores", "major_concerns", "ai_authorship", "recommendation"],
    "additionalProperties": True,
}


@dataclass
class Review:
    """A single reviewer's structured critique."""
    reviewer_id: str
    reviewer_name: str
    provider: str
    model: str
    payload: dict[str, Any]                 # the parsed JSON body (schema above)
    raw_text: str = ""                      # original model output, for audit
    error: str | None = None                # set if the call or parse failed

    @property
    def ok(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict[str, Any]:
        return {
            "reviewer_id": self.reviewer_id,
            "reviewer_name": self.reviewer_name,
            "provider": self.provider,
            "model": self.model,
            "error": self.error,
            "review": self.payload,
            "raw_text": self.raw_text,
        }


def extract_json(text: str) -> dict[str, Any]:
    """Pull the first balanced top-level JSON object out of ``text``.

    Models sometimes wrap JSON in prose or ```json fences despite instructions; this
    finds the outermost {...} and parses it. Raises ValueError if none parses.
    """
    if not text:
        raise ValueError("empty response")
    # fast path
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            c = text[i]
            if in_str:
                if esc:
                    esc = False
                elif c == "\\":
                    esc = True
                elif c == '"':
                    in_str = False
            else:
                if c == '"':
                    in_str = True
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i + 1])
                        except json.JSONDecodeError:
                            break
        start = text.find("{", start + 1)
    raise ValueError("no parseable JSON object found in response")


_LIST_FIELDS = ("major_concerns", "minor_concerns", "blind_spots", "inconsistencies",
                "missing_prior_art", "suggested_experiments", "questions_for_authors")


def parse_review(reviewer_id: str, reviewer_name: str, provider: str, model: str,
                 raw_text: str) -> Review:
    """Parse a model's raw output into a Review, normalizing missing fields."""
    try:
        payload = extract_json(raw_text)
    except ValueError as e:
        return Review(reviewer_id, reviewer_name, provider, model,
                      payload={}, raw_text=raw_text, error=f"parse: {e}")
    # soft-normalize so downstream code can assume keys exist
    for f in _LIST_FIELDS:
        payload.setdefault(f, [])
    payload.setdefault("ai_authorship", {"overall_likelihood": None,
                                         "confidence": "low", "tells": []})
    payload.setdefault("scores", {})
    payload.setdefault("recommendation", "major_revision")
    return Review(reviewer_id, reviewer_name, provider, model,
                  payload=payload, raw_text=raw_text)
