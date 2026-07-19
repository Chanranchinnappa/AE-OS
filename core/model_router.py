"""Model Router — 07_TECH_STACK_AND_INFRA.md + 11_TOKEN_OPTIMIZATION.md.

Every LLM call in AE-OS goes through route(). Policy:
  Tier 0 (free/local, default)  -> Ollama or free-tier open models
  Tier 1 (free/cheap API)       -> only after Tier 0 fails a quality check
  Tier 2 (premium)              -> only after Tier 0 AND Tier 1 failed on the
                                   same task, or task_class is high-stakes;
                                   always with a logged justification.

Every call is logged to the Ledger: model, tokens in/out, cost, tier, and
justification if Tier > 0. Providers are pluggable; ships with an Ollama
provider and a dry-run echo provider so the loop can run with zero spend.
"""
from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from memory.ledger import Ledger
from . import kill_switch

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "settings.json"

HIGH_STAKES_CLASSES = {"legal_risk", "financial_modeling", "deploy_decision",
                       "ceo_conflict_resolution"}


class RouterError(Exception):
    pass


class EscalationDenied(RouterError):
    """Raised when a tier escalation violates policy."""


@dataclass
class ModelResponse:
    text: str
    model: str
    tier: int
    tokens_in: int = 0
    tokens_out: int = 0
    cost_currency: float = 0.0


@dataclass
class RouterConfig:
    tier0_provider: str = "dry_run"          # 'ollama' once installed
    tier0_model: str = "llama3.2"
    ollama_url: str = "http://localhost:11434"
    tier1_provider: str = "none"             # wire a free-tier API here later
    tier2_provider: str = "none"             # premium; requires justification
    daily_currency_ceiling: float = 0.0      # near-zero budget: default 0

    @classmethod
    def load(cls) -> "RouterConfig":
        if CONFIG_PATH.exists():
            data = json.loads(CONFIG_PATH.read_text()).get("model_router", {})
            return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
        return cls()


def _dry_run_provider(prompt: str, model: str, url: str) -> ModelResponse:
    """Zero-cost stand-in so the system runs end-to-end before Ollama is set up."""
    return ModelResponse(
        text=f"[dry-run:{model}] would answer: {prompt[:120]}",
        model=f"dry-run/{model}", tier=0,
        tokens_in=len(prompt) // 4, tokens_out=32,
    )


def _ollama_provider(prompt: str, model: str, url: str) -> ModelResponse:
    req = urllib.request.Request(
        f"{url}/api/generate",
        data=json.dumps({"model": model, "prompt": prompt, "stream": False}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.loads(r.read())
    return ModelResponse(
        text=data.get("response", ""), model=f"ollama/{model}", tier=0,
        tokens_in=data.get("prompt_eval_count", 0),
        tokens_out=data.get("eval_count", 0),
    )


PROVIDERS: dict[str, Callable[..., ModelResponse]] = {
    "dry_run": _dry_run_provider,
    "ollama": _ollama_provider,
}


class ModelRouter:
    def __init__(self, ledger: Ledger | None = None, config: RouterConfig | None = None):
        self.ledger = ledger or Ledger()
        self.config = config or RouterConfig.load()
        # failure memory per task_id, used to authorize escalation
        self._failures: dict[str, list[int]] = {}

    def record_failure(self, task_id: str, tier: int) -> None:
        self._failures.setdefault(task_id, []).append(tier)

    def _authorize_tier(self, task_id: str, requested: int, task_class: str) -> str:
        """Return justification string, or raise EscalationDenied."""
        fails = self._failures.get(task_id, [])
        if requested == 0:
            return "default tier"
        if requested == 1:
            if 0 in fails:
                return f"Tier 0 failed quality check on task {task_id}"
            raise EscalationDenied("Tier 1 requires a recorded Tier 0 failure")
        if requested == 2:
            if task_class in HIGH_STAKES_CLASSES:
                return f"high-stakes task class: {task_class}"
            if 0 in fails and 1 in fails:
                return f"Tier 0 and Tier 1 both failed on task {task_id}"
            raise EscalationDenied(
                "Tier 2 requires Tier 0 AND Tier 1 failures, or a high-stakes task class"
            )
        raise RouterError(f"Unknown tier: {requested}")

    def route(
        self,
        prompt: str,
        agent_id: str,
        department: str,
        task_id: str,
        task_class: str = "routine",
        tier: int = 0,
    ) -> ModelResponse:
        kill_switch.guard()  # nothing runs while the Chairperson has paused the system

        justification = self._authorize_tier(task_id, tier, task_class)

        if tier == 0:
            provider_name = self.config.tier0_provider
        elif tier == 1:
            provider_name = self.config.tier1_provider
        else:
            provider_name = self.config.tier2_provider

        provider = PROVIDERS.get(provider_name)
        if provider is None:
            raise RouterError(
                f"No provider wired for tier {tier} ('{provider_name}'). "
                "Configure config/settings.json."
            )

        resp = provider(prompt, self.config.tier0_model, self.config.ollama_url)
        resp.tier = tier

        self.ledger.log(
            department=department,
            agent_id=agent_id,
            action_type="model_call",
            status="success",
            inputs={"task_id": task_id, "task_class": task_class,
                    "prompt_chars": len(prompt)},
            outputs={"model": resp.model, "tier": tier,
                     "justification": justification if tier > 0 else None},
            cost_tokens=resp.tokens_in + resp.tokens_out,
            cost_currency=resp.cost_currency,
        )
        return resp
