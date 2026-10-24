"""Agent framework for hey ops.

An Agent is a lane (cs, ar, ap, board, close, onboarding) with a system
prompt, a set of Tools and a review policy. Running an agent on a WorkItem
produces a Proposal. Read-risk tools execute immediately while the agent
thinks; write/send/money tools become the Proposal and wait for a person
unless policy lets the lane execute on its own.

Two modes: `demo` (deterministic planners, no API key) and `live` (Claude
with tool use). Both produce the same Proposal shape so the console and the
tests do not care which ran.
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Callable

from flask import current_app

from ..extensions import db
from ..models import AgentRun, WorkItem

log = logging.getLogger(__name__)

RISK_READ, RISK_WRITE, RISK_SEND, RISK_MONEY = "read", "write", "send", "money"


@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict
    fn: Callable[..., dict]
    risk: str = RISK_READ

    def spec(self) -> dict:
        return {"name": self.name, "description": self.description, "input_schema": self.input_schema}


@dataclass
class Proposal:
    action: str
    payload: dict = field(default_factory=dict)
    preview: str = ""
    confidence: float = 0.5
    sources: list = field(default_factory=list)
    reason: str = ""
    needs_review: bool = True

    def to_json(self) -> dict:
        return asdict(self)


class Agent:
    lane = "base"
    name = "agent"
    description = ""
    system_prompt = ""
    tools: list[Tool] = []
    # lanes where the agent may execute send/write tools without review when shadow mode is off
    auto_execute_risks: set[str] = {RISK_READ}

    # ---- public --------------------------------------------------------
    def run(self, item: WorkItem) -> Proposal:
        t0 = time.time()
        mode = "live" if current_app.config.get("ANTHROPIC_API_KEY") else "demo"
        try:
            proposal = self.run_live(item) if mode == "live" else self.plan(item)
        except Exception as e:  # noqa: BLE001
            log.exception("agent %s failed on item %s", self.lane, item.id)
            proposal = Proposal(action="escalate", payload={"lane": "coordinator", "note": f"agent error: {e}"}, preview=f"Agent error, escalating: {e}", reason="exception")
        proposal.needs_review = self.needs_review(item, proposal)
        db.session.add(AgentRun(work_item_id=item.id, lane=self.lane, mode=mode, step=99, tool=proposal.action, input=(item.summary or "")[:2000], output=proposal.preview[:4000], ms=int((time.time() - t0) * 1000)))
        return proposal

    def execute(self, item: WorkItem, proposal: dict) -> dict:
        tool = self.tool(proposal.get("action"))
        if tool is None:
            return {"ok": False, "error": f"unknown action {proposal.get('action')}"}
        t0 = time.time()
        result = tool.fn(item=item, **(proposal.get("payload") or {}))
        db.session.add(AgentRun(work_item_id=item.id, lane=self.lane, mode="execute", step=100, tool=tool.name, input=json.dumps(proposal.get("payload") or {})[:2000], output=json.dumps(result, default=str)[:4000], ms=int((time.time() - t0) * 1000)))
        return result

    # ---- policy ----------------------------------------------------------
    def needs_review(self, item: WorkItem, proposal: Proposal) -> bool:
        if proposal.action in ("none", "handoff", "escalate"):  # routing, not acting
            return False
        tool = self.tool(proposal.action)
        risk = tool.risk if tool else RISK_SEND
        if risk == RISK_READ:  # reads never need a person
            return False
        if item.shadow or current_app.config.get("SHADOW_MODE", True):
            return True
        if risk == RISK_MONEY:
            return True
        if risk not in self.auto_execute_risks:
            return True
        return proposal.confidence < current_app.config.get("AUTO_CONFIDENCE", 0.8)

    # ---- helpers -----------------------------------------------------------
    def tool(self, name: str | None) -> Tool | None:
        return next((t for t in self.tools if t.name == name), None)

    def plan(self, item: WorkItem) -> Proposal:  # demo-mode planner; subclasses override
        return Proposal(action="escalate", payload={"lane": "coordinator", "note": "no planner"}, preview="No planner for this lane.", reason="demo")

    def context(self, item: WorkItem) -> str:  # text context for the live model; subclasses extend
        return f"Work item #{item.id} · lane {self.lane} · kind {item.kind} · community {item.community_id} · subject: {item.subject}\n\n{item.summary or ''}"

    # ---- live mode: Claude with tools ---------------------------------------
    def run_live(self, item: WorkItem, max_steps: int = 6) -> Proposal:
        import anthropic

        client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])
        model = current_app.config.get("HEY_AI_MODEL", "claude-opus-5-5")
        messages: list[dict] = [{"role": "user", "content": self.context(item)}]
        system = self.system_prompt + "\n\nYou may call read tools freely. Any tool that sends, writes or moves money is a PROPOSAL: call it once with the final payload and stop; a person reviews it. If nothing should be done, say so in one line and call no tool."
        for step in range(max_steps):
            resp = client.beta.messages.create(
                model=model, max_tokens=4000, betas=["server-side-fallback-2026-07-01"], fallbacks="default",
                output_config={"effort": "medium"},
                system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
                tools=[t.spec() for t in self.tools], messages=messages,
            )
            db.session.add(AgentRun(work_item_id=item.id, lane=self.lane, mode="live", step=step, tool=",".join(b.name for b in resp.content if b.type == "tool_use") or "text", input="", output="".join(b.text for b in resp.content if b.type == "text")[:4000], tokens_in=getattr(resp.usage, "input_tokens", 0), tokens_out=getattr(resp.usage, "output_tokens", 0)))
            if resp.stop_reason == "refusal":
                return Proposal(action="escalate", payload={"lane": "coordinator", "note": "model refused"}, preview="Model declined; routing to a person.", reason="refusal")
            tool_uses = [b for b in resp.content if b.type == "tool_use"]
            text = "".join(b.text for b in resp.content if b.type == "text").strip()
            if not tool_uses:
                return Proposal(action="none", preview=text or "Nothing to do.", confidence=0.9, reason="no action")
            messages.append({"role": "assistant", "content": resp.content})
            results = []
            for tu in tool_uses:
                tool = self.tool(tu.name)
                if tool is None:
                    results.append({"type": "tool_result", "tool_use_id": tu.id, "content": "unknown tool", "is_error": True})
                    continue
                if tool.risk == RISK_READ:
                    try:
                        out = tool.fn(item=item, **(tu.input or {}))
                    except Exception as e:  # noqa: BLE001
                        out = {"error": str(e)}
                    results.append({"type": "tool_result", "tool_use_id": tu.id, "content": json.dumps(out, default=str)[:8000]})
                else:
                    payload = dict(tu.input or {})
                    return Proposal(action=tool.name, payload=payload, preview=text or self.preview_for(tool, payload), confidence=0.8, reason="model proposal")
            messages.append({"role": "user", "content": results})
        return Proposal(action="escalate", payload={"lane": "coordinator", "note": "step limit"}, preview="Agent hit its step limit; routing to a person.", reason="limit")

    def preview_for(self, tool: Tool, payload: dict) -> str:
        return f"{tool.name}: " + json.dumps(payload, default=str)[:800]
