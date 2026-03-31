import re

LLM_CREDIT_ERROR_PATTERNS = [
    r"(?i)free\s+usage\s+exceeded",
    r"(?i)add\s+credits?",
    r"(?i)insufficient\s+credits?",
    r"(?i)credit\s+exhausted",
    r"(?i)billing\s+(?:required|error|issue|missing|info)",
    r"(?i)payment\s+(?:required|failed|method|issue)",
    r"(?i)account\s+(?:suspended|disabled|overdue|restricted)",
    r"(?i)quota\s+exceeded",
    r"(?i)usage\s+limit\s+(?:exceeded|reached)",
    r"(?i)balance\s+(?:insufficient|too\s+low|zero|negative)",
    r"(?i)upgrade\s+(?:required|your\s+plan|to\s+continue)",
    r"(?i)402\s+Payment\s+Required",
    r"(?i)403\s+.*(?:forbidden|credit|billing|usage)",
]

_COMPILED_PATTERNS = [re.compile(p) for p in LLM_CREDIT_ERROR_PATTERNS]


def is_llm_credit_error(error_message: str) -> bool:
    if not error_message:
        return False
    return any(p.search(error_message) for p in _COMPILED_PATTERNS)


def classify_llm_error(error_message: str) -> str:
    if is_llm_credit_error(error_message):
        return "credit_exhausted"
    if any(
        kw in error_message.lower() for kw in ["rate limit", "too many requests", "429"]
    ):
        return "rate_limited"
    if any(kw in error_message.lower() for kw in ["timeout", "timed out", "deadline"]):
        return "timeout"
    if any(
        kw in error_message.lower() for kw in ["connection", "unreachable", "network"]
    ):
        return "connection_error"
    if any(
        kw in error_message.lower()
        for kw in ["authentication", "api key", "unauthorized", "401"]
    ):
        return "authentication_error"
    if any(
        kw in error_message.lower()
        for kw in ["context length", "max tokens", "token limit", "too long"]
    ):
        return "context_length_exceeded"
    return "unknown"
