"""Detects intent and extracts entities from a customer's message.

Tries the LLM first for intent classification; falls back to plain
keyword matching if the LLM is slow, errors, or returns something that
isn't a recognized intent. FAQ answers are canned text, never LLM
output -- the LLM only ever classifies intent here, it doesn't decide
anything.
"""

import re

from app.agents.base_agent import BaseAgent
from app.config import settings
from app.llm import ask_llm

VALID_INTENTS = {"refund", "product_search", "faq", "unknown"}

# Only these count as a confident LLM classification. A reply of
# "unknown" (or anything unparseable) is treated as the LLM being
# unsure, which triggers the keyword fallback rather than being
# accepted as-is -- phi-2 is small enough that its "unknown" often
# just means it couldn't parse the message at all.
LLM_ACCEPTABLE_INTENTS = {"refund", "product_search", "faq"}

# Checked before any LLM/keyword intent detection -- if a message matches
# one of these topics, we can answer directly without routing anywhere.
FAQ_ANSWERS = {
    "return policy": "You can return most items within 30 days of purchase for a full refund.",
    "shipping": "Standard shipping takes 3-5 business days.",
    "contact": "You can reach our support team through this chat, 24/7.",
    "payment": "We accept all major credit cards and PayPal.",
}

KEYWORD_INTENT_MAP = {
    "refund": ["refund", "return", "money back", "cancel my order"],
    "product_search": ["looking for", "search", "recommend", "do you have", "buy"],
}

# Friendly canned reply describing what the assistant can do; reused by the
# orchestrator's "not sure" fallback too.
CAPABILITIES_REPLY = (
    "I can help you a few ways:\n"
    '- Find products — e.g. "show me warm jackets"\n'
    '- Process a refund — e.g. "I want a refund for order #12"\n'
    "- Answer questions about returns, shipping, and payment."
)

# Greetings / small-talk get an instant canned reply (no model call). Word
# boundaries avoid false matches like "hi" inside "shipping". These are only
# used when the message carries no task signal (see _has_task_signal).
SMALLTALK_PATTERNS = [
    (
        re.compile(r"\b(hi|hello|hey|hiya|howdy|greetings|good\s+(morning|afternoon|evening))\b"),
        "Hello! 👋 I'm your shopping assistant. I can help you find products, "
        "check our policies, or process a refund. What can I help you with?",
    ),
    (
        re.compile(r"\b(thank you|thanks|thankyou|thx|appreciate)\b"),
        "You're welcome! Is there anything else I can help you with?",
    ),
    (
        re.compile(r"\b(who are you|what are you|your name)\b"),
        "I'm the store's AI assistant. I can help with product searches, refunds, "
        "and questions about our policies.",
    ),
    (re.compile(r"\b(what can you do|how can you help|what do you do)\b"), CAPABILITIES_REPLY),
    (
        re.compile(r"\b(bye|goodbye|see you|see ya|cya)\b"),
        "Thanks for stopping by! Have a great day. 😊",
    ),
]

ORDER_ID_PATTERN = re.compile(r"order\s*#?\s*(\d+)", re.IGNORECASE)

INTENT_PROMPT = (
    'Classify the intent of this customer message as exactly one word: '
    'refund, product_search, faq, or unknown.\n'
    'Message: "{message}"\n'
    'Intent:'
)


class SupportAgent(BaseAgent):
    name = "support_agent"
    # Must stay above the intent call's own timeout (below) so the base
    # agent never kills the LLM call mid-flight -- we want a slow LLM to
    # fall back to keywords, not to blow up the whole agent.
    timeout_seconds = 30.0
    intent_llm_timeout = 20

    def process(self, message: str) -> dict:
        faq_answer = self._match_faq(message)
        if faq_answer:
            return {"intent": "faq", "answer": faq_answer, "entities": {}, "method": "keyword"}

        # Greetings / small-talk: answer instantly (no model call), but only
        # when the message has no task signal, so "hi, need a refund for
        # order 5" still routes to the refund flow instead of just saying hi.
        if not self._has_task_signal(message):
            smalltalk = self._match_smalltalk(message)
            if smalltalk:
                return {
                    "intent": "smalltalk",
                    "answer": smalltalk,
                    "entities": {},
                    "method": "keyword",
                }

        # In safe mode the LLM is skipped entirely and we go straight to
        # keyword matching.
        intent = self._detect_intent_via_llm(message) if settings.use_llm else None
        if intent is not None:
            method = "llm"
        else:
            intent = self._detect_intent_via_keywords(message)
            method = "keyword"

        return {"intent": intent, "entities": self._extract_entities(message), "method": method}

    def _match_faq(self, message: str) -> str | None:
        lowered = message.lower()
        for topic, answer in FAQ_ANSWERS.items():
            if topic in lowered:
                return answer
        return None

    def _match_smalltalk(self, message: str) -> str | None:
        lowered = message.lower().strip()
        for pattern, reply in SMALLTALK_PATTERNS:
            if pattern.search(lowered):
                return reply
        return None

    def _has_task_signal(self, message: str) -> bool:
        """True if the message looks like an actual task (a refund/product
        request or an order number), in which case it should be routed
        normally rather than treated as small-talk."""
        lowered = message.lower()
        for keywords in KEYWORD_INTENT_MAP.values():
            if any(keyword in lowered for keyword in keywords):
                return True
        return bool(ORDER_ID_PATTERN.search(message))

    def _detect_intent_via_llm(self, message: str) -> str | None:
        """Return a confident intent, or None if the LLM's reply wasn't
        one of the three substantive intents (this is what triggers the
        keyword fallback)."""
        # Only a handful of tokens are needed for a one-word classification,
        # which also keeps this call faster than a full 256-token reply.
        reply = ask_llm(
            INTENT_PROMPT.format(message=message),
            max_tokens=10,
            timeout=self.intent_llm_timeout,
        )
        first_word = reply.strip().lower().split()[0].strip(".,!\"'") if reply.strip() else ""
        return first_word if first_word in LLM_ACCEPTABLE_INTENTS else None

    def _detect_intent_via_keywords(self, message: str) -> str:
        lowered = message.lower()
        for intent, keywords in KEYWORD_INTENT_MAP.items():
            if any(keyword in lowered for keyword in keywords):
                return intent
        return "unknown"

    def _extract_entities(self, message: str) -> dict:
        entities = {}
        order_match = ORDER_ID_PATTERN.search(message)
        if order_match:
            entities["order_id"] = int(order_match.group(1))
        # No structured product-name extraction yet -- the Product Agent's
        # semantic search takes a free-text query, so the raw message works
        # as-is for now.
        entities["product_query"] = message
        return entities
