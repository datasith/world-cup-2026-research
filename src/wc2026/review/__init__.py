"""LLM-as-judge reviewer panel for the manuscript.

Three expert-persona reviewers, each backed by a different model family (Anthropic,
OpenAI, Google), critique the project documents and the manuscript: novelty, rigor,
methodology, internal consistency, blind spots -- and whether the prose reads as
AI-generated. Personas live as editable markdown in ``reviewers/`` (prompt-as-data);
providers are swappable behind a common interface; secrets come from the environment.

Entry point: ``scripts/run_review.py`` -> :func:`orchestrator.run_panel`.
"""
from .schema import REVIEW_JSON_SCHEMA, Review, parse_review

__all__ = ["REVIEW_JSON_SCHEMA", "Review", "parse_review"]
