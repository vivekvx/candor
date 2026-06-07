import logging
import re
from typing import NamedTuple

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    (r'ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|prompts?|context)', 'instruction_override'),
    (r'disregard\s+(the\s+)?(above|previous|prior|all)', 'instruction_override'),
    (r'forget\s+(everything|all|what)', 'instruction_override'),
    (r'new\s+instructions?\s*:', 'instruction_override'),
    (r'updated\s+instructions?\s*:', 'instruction_override'),
    (r'you\s+are\s+now\s+(a|an|the)?\s*\w+', 'role_hijack'),
    (r'you\s+are\s+DAN\b', 'role_hijack'),
    (r'act\s+as\s+(if|a|an|the)', 'role_hijack'),
    (r'pretend\s+(you\s+are|to\s+be)', 'role_hijack'),
    (r'your\s+new\s+(role|persona|identity)\s+is', 'role_hijack'),
    (r'(reveal|show|print|output|display)\s+(your\s+)?(system\s+prompt|instructions)', 'extraction'),
    (r'what\s+(are\s+your|is\s+your)\s+(instructions?|system\s+prompt)', 'extraction'),
    (r'repeat\s+(everything|above|all)', 'extraction'),
    (r'(output|print|show)\s+everything', 'extraction'),
    (r'show\s+your\s+instructions', 'extraction'),
    (r'what\s+were\s+you\s+told', 'extraction'),
    (r'\bverbatim\b', 'extraction'),
    (r'<\|.*?\|>', 'token_injection'),
    (r'\[INST\].*?\[\/INST\]', 'token_injection'),
    (r'<\/?s>', 'token_injection'),
    (r'<<SYS>>.*?<</SYS>>', 'token_injection'),
    (r'(always|must|should)\s+(rate|score|give)\s+(this(?:\s+company)?|the\s+company)\s+(10|10\/10|perfect|maximum)', 'score_manipulation'),
    (r'(ignore|disregard)\s+(any|all)\s+(negative|bad|concerning)\s+(signals?|data|information)', 'score_manipulation'),
    (r'\b(set|change)\s+(bull_score|bear_score|score|confidence)\b', 'score_manipulation'),
    (r'\bbull_score\b|\bbear_score\b', 'score_manipulation'),
    (r'(score|confidence)\s+to\s+[0-9]', 'score_manipulation'),
]


class SanitizationResult(NamedTuple):
    cleaned_text: str
    was_sanitized: bool
    patterns_found: list[str]
    removed_count: int


def sanitize_web_content(text: str) -> SanitizationResult:
    """Strip prompt injection patterns from web-scraped content."""
    if not text:
        return SanitizationResult(text, False, [], 0)

    cleaned = text
    patterns_found = []
    removed_count = 0

    for pattern, attack_type in INJECTION_PATTERNS:
        matches = re.findall(pattern, cleaned, re.IGNORECASE | re.DOTALL)
        if matches:
            cleaned = re.sub(pattern, '[REDACTED]', cleaned, flags=re.IGNORECASE | re.DOTALL)
            patterns_found.append(attack_type)
            removed_count += len(matches)

    was_sanitized = removed_count > 0

    if was_sanitized:
        logger.warning(
            "Prompt injection detected and sanitized. Patterns: %s. Removed %d matches.",
            patterns_found, removed_count,
        )

    return SanitizationResult(
        cleaned_text=cleaned,
        was_sanitized=was_sanitized,
        patterns_found=patterns_found,
        removed_count=removed_count,
    )


def was_sanitized(original: str, cleaned: str) -> bool:
    """Compatibility shim for callers using the old two-arg API."""
    changed = original != cleaned
    if changed:
        logger.warning("Prompt injection pattern detected and stripped from web content")
    return changed
