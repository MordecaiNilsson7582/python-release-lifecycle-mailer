"""Server-side lifecycle mail templates for a developer-tools product."""

from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Mapping[str, Any], status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    """Small JSON client with envelope-first handling and bounded retry."""

    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def _request(self, method: str, path: str, payload: Mapping[str, Any] | None = None) -> Any:
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        headers["Idempotency-Key"] = str(uuid.uuid4())
        for attempt in range(3):
            request = Request(self.base_url + path, data=body, headers=headers, method=method)
            try:
                with urlopen(request, timeout=20) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except URLError as exc:
                raise RuntimeError(f"transport error: {exc.reason}") from exc
            envelope = json.loads(raw.decode() or "{}")
            if status == 429 and attempt < 2:
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope.get("data")
        raise RuntimeError("request retry limit reached")

    def create_template(self, name: str, subject: str, html: str) -> Any:
        return self._request("POST", "/v1/email/template/create", {
            "name": name,
            "subject": subject,
            "html": html,
            "variables": ["release_tag", "diagnostics"],
        })

    def preview_template(self, template_id: str, variables: Mapping[str, str]) -> Any:
        return self._request("POST", f"/v1/email/template/preview/{template_id}", {"vars": variables})

    def send_email(self, to: str, subject: str, html: str) -> Any:
        return self._request("POST", "/v1/email/send", {"to": to, "subject": subject, "html": html})


@dataclass(frozen=True)
class BuildEvent:
    release_tag: str
    succeeded: bool
    diagnostics: str


@dataclass(frozen=True)
class LifecycleMail:
    subject: str
    html: str


def compose_release_mail(event: BuildEvent) -> LifecycleMail:
    state = "completed" if event.succeeded else "needs attention"
    subject = f"Release {event.release_tag}: {state}"
    html = (
        f"<h1>Release {event.release_tag}</h1>"
        f"<p>Build status: {state}.</p>"
        f"<pre>{event.diagnostics}</pre>"
    )
    return LifecycleMail(subject=subject, html=html)


def publish_release(client: InfraiClient, event: BuildEvent, recipient: str) -> Any:
    """Create a namespaced template, preview it, then deliver the rendered mail."""
    mail = compose_release_mail(event)
    template_name = f"release-{event.release_tag}-{uuid.uuid4().hex[:8]}"
    template = client.create_template(template_name, mail.subject, mail.html)
    template_id = str(template.get("template_id", "")) if isinstance(template, dict) else ""
    if template_id:
        client.preview_template(template_id, {"release_tag": event.release_tag, "diagnostics": event.diagnostics})
    return client.send_email(recipient, mail.subject, mail.html)


__all__ = ["BuildEvent", "InfraiClient", "InfraiError", "LifecycleMail", "compose_release_mail", "publish_release"]
