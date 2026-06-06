import logging
import re

logger = logging.getLogger(__name__)

INJECTION_PATTERNS = [
    r'ignore\s+(all\s+)?previous\s+instructions?',
    r'disregard\s+the\s+above',
    r'you\s+are\s+now\s+a',
    r'new\s+instruction[s]?:',
    r'system\s+prompt:',
    r'forget\s+everything',
    r'act\s+as\s+if',
    r'<\|.*?\|>',
    r'\[INST\].*?\[\/INST\]',
]

_compiled = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in INJECTION_PATTERNS]


def sanitize_web_content(text: str) -> str:
    """Strip prompt injection patterns from web content."""
    for pattern in _compiled:
        text = pattern.sub('', text)
    return text


def was_sanitized(original: str, cleaned: str) -> bool:
    changed = original != cleaned
    if changed:
        logger.warning("Prompt injection pattern detected and stripped from web content")
    return changed
