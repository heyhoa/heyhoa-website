"""Help Scout Mailbox API 2.0 client and webhook verification.

Help Scout is both the shared inbox and the ticket system (doc 13). Each
community gets an alias that lands in the support mailbox; the sales mailbox
receives quote requests and contact-form messages.

Auth: OAuth2 client credentials (App ID / App Secret from Help Scout → My Apps).
Webhooks: HMAC-SHA1 of the raw body with the webhook secret, base64, in the
`X-HelpScout-Signature` header; event name in `X-HelpScout-Event`.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
from typing import Any

import requests

log = logging.getLogger(__name__)

API = "https://api.helpscout.net/v2"


class HelpScoutError(RuntimeError):
    pass


class HelpScoutClient:
    def __init__(self, app_id: str, app_secret: str, timeout: int = 20, session: requests.Session | None = None):
        self.app_id, self.app_secret, self.timeout = app_id, app_secret, timeout
        self.s = session or requests.Session()
        self._token: str | None = None
        self._token_exp = 0.0

    # ---- auth ----------------------------------------------------------
    def token(self) -> str:
        if self._token and time.time() < self._token_exp - 60:
            return self._token
        r = self.s.post(f"{API}/oauth2/token", data={"grant_type": "client_credentials", "client_id": self.app_id, "client_secret": self.app_secret}, timeout=self.timeout)
        if r.status_code >= 400:
            raise HelpScoutError(f"token: {r.status_code} {r.text[:200]}")
        j = r.json()
        self._token = j["access_token"]
        self._token_exp = time.time() + int(j.get("expires_in", 172800))
        return self._token

    def _req(self, method: str, path: str, **kw) -> Any:
        headers = {"Authorization": f"Bearer {self.token()}", "Content-Type": "application/json"}
        r = self.s.request(method, f"{API}{path}", headers=headers, timeout=self.timeout, **kw)
        if r.status_code == 401:  # token revoked; refresh once
            self._token = None
            headers["Authorization"] = f"Bearer {self.token()}"
            r = self.s.request(method, f"{API}{path}", headers=headers, timeout=self.timeout, **kw)
        if r.status_code >= 400:
            raise HelpScoutError(f"{method} {path}: {r.status_code} {r.text[:300]}")
        if r.status_code == 201 and "Resource-ID" in r.headers:
            return {"id": int(r.headers["Resource-ID"])}
        return r.json() if r.content else None

    # ---- conversations -------------------------------------------------
    def create_conversation(self, mailbox_id: int, subject: str, customer_email: str, text: str, *, first_name: str = "", last_name: str = "",
                            tags: list[str] | None = None, status: str = "active", assign_to: int | None = None, imported: bool = False, thread_type: str = "customer") -> dict:
        body: dict[str, Any] = {
            "subject": subject, "type": "email", "mailboxId": mailbox_id, "status": status,
            "customer": {"email": customer_email, **({"firstName": first_name} if first_name else {}), **({"lastName": last_name} if last_name else {})},
            "threads": [{"type": thread_type, "customer": {"email": customer_email}, "text": text}],
            "imported": imported,
        }
        if tags:
            body["tags"] = tags
        if assign_to:
            body["assignTo"] = assign_to
        return self._req("POST", "/conversations", json=body)

    def get_conversation(self, conversation_id: int, embed_threads: bool = True) -> dict:
        return self._req("GET", f"/conversations/{conversation_id}", params={"embed": "threads"} if embed_threads else None)

    def list_conversations(self, mailbox_id: int, status: str = "active", page: int = 1) -> dict:
        return self._req("GET", "/conversations", params={"mailbox": mailbox_id, "status": status, "page": page})

    def reply(self, conversation_id: int, customer_email: str, text: str, *, draft: bool = False, status: str | None = None) -> dict:
        body: dict[str, Any] = {"customer": {"email": customer_email}, "text": text, "draft": draft}
        if status:
            body["status"] = status
        return self._req("POST", f"/conversations/{conversation_id}/reply", json=body)

    def note(self, conversation_id: int, text: str) -> dict:
        return self._req("POST", f"/conversations/{conversation_id}/notes", json={"text": text})

    def set_tags(self, conversation_id: int, tags: list[str]) -> None:
        self._req("PUT", f"/conversations/{conversation_id}/tags", json={"tags": tags})

    def assign(self, conversation_id: int, user_id: int | None) -> None:
        self._req("PATCH", f"/conversations/{conversation_id}", json={"op": "replace", "path": "/assignTo", "value": user_id})

    def set_status(self, conversation_id: int, status: str) -> None:
        self._req("PATCH", f"/conversations/{conversation_id}", json={"op": "replace", "path": "/status", "value": status})

    def find_customer(self, email: str) -> dict | None:
        j = self._req("GET", "/customers", params={"query": f'(email:"{email}")'})
        items = (j or {}).get("_embedded", {}).get("customers", [])
        return items[0] if items else None


def verify_signature(raw_body: bytes, signature: str | None, secret: str) -> bool:
    if not signature or not secret:
        return False
    digest = base64.b64encode(hmac.new(secret.encode(), raw_body, hashlib.sha1).digest()).decode()
    return hmac.compare_digest(digest, signature.strip())


def extract_customer_email(conversation: dict) -> str:
    c = conversation.get("primaryCustomer") or conversation.get("customer") or {}
    return (c.get("email") or "").lower()


def extract_latest_customer_text(conversation: dict) -> str:
    threads = (conversation.get("_embedded") or {}).get("threads") or conversation.get("threads") or []
    for t in reversed(threads):
        if t.get("type") == "customer":
            return t.get("body") or t.get("text") or ""
    return conversation.get("preview") or ""


def extract_to_addresses(conversation: dict) -> list[str]:
    out = []
    threads = (conversation.get("_embedded") or {}).get("threads") or conversation.get("threads") or []
    for t in threads:
        for a in (t.get("to") or []):
            out.append(str(a).lower())
    for a in (conversation.get("cc") or []):
        out.append(str(a).lower())
    return out
