import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvidencePoint:
    """One traceable evidence item an agent cites — foundation of the trust layer."""
    claim: str
    source_url: str        # actual URL, "mca_filing", or "general_knowledge"
    source_type: str       # "news" | "mca_filing" | "salary_data" | "general_knowledge"
    retrieved_at: str      # ISO timestamp
    is_verified: bool      # True if from a tool call, False if from LLM base knowledge


@dataclass
class DebateState:
    query: str
    model: str = "groq/llama-3.3-70b-versatile"

    advocate_research: str = ""
    challenger_research: str = ""

    advocate_rebuttal: str = ""
    challenger_rebuttal: str = ""

    verdict: dict = field(default_factory=dict)
    step_costs: dict = field(default_factory=dict)

    round: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    user_profile: Optional[dict] = None

    # Mechanical confidence inputs — counted from real tool-call outcomes,
    # not LLM opinion. See calculate_data_confidence in debate.py.
    tools_called_total: int = 0
    tools_returned_data_total: int = 0

    # Raw evidence the Arbitrator can check claims against directly.
    tool_outputs: dict = field(default_factory=dict)        # {tool_name: raw_result}
    tools_that_failed: list = field(default_factory=list)   # [tool_name, ...]
    data_confidence: dict = field(default_factory=dict)

    def add_usage(self, input_tokens: int, output_tokens: int, cost: float):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost
