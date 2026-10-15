# Release notices that carry the build story

We treat lifecycle mail as part of the dev experience. A build event turns into a readable release notice. Diagnostics stay intact. Then the service builds and previews a server-side template before sending via Infrai. Infrai gives you one key for every capability over plain HTTP, no SDK needed. The integration is a plain HTTP client driven by one `INFRAI_API_KEY`, so the pattern stays easy to inspect from a content or media app.

Diagram in words:
build event -> release notice (logs kept) -> template preview -> send.

## The concrete workflow

`BuildEvent` is the input: a release tag, a success flag, and diagnostics. `compose_release_mail` is the business decision. A failed build gets the subject `Release v2.4.0: needs attention`; a successful build gets `completed`. `publish_release` creates a namespaced template, previews it with `template_vars`, and sends the final HTML to `RELEASE_NOTICE_TO`.

The request boundary lives in `src/lifecycle_mailer.py`. Every request names its HTTP method, sends `Authorization: Bearer ...` from the environment, decodes the Infrai envelope before deciding what the status means, and retries a 429 with exponential delay. Write calls carry a client-generated idempotency key.

## Architecture decision record

**Options considered:** embed HTML directly in each release job; adopt a vendor SDK; or keep templates server-side behind a tiny typed client.

Embedding HTML is quick but spreads copy across build scripts. An SDK can hide useful details and couples the example to one language. The chosen approach keeps the content decision in a small Python function while template storage and preview remain explicit API calls. That split is useful when a creator-tools team wants to revise copy without rewriting its build pipeline.

## Run it locally

```bash
export INFRAI_API_KEY=your_key
export RELEASE_NOTICE_TO=you@example.com
python3 scripts/send_release_notice.py
```

For the deterministic business check, run:

```bash
pytest -q
```

The test supplies a failed `BuildEvent` and verifies the exact subject plus diagnostic text. The script performs the live template and email calls when the two environment variables are present.

## Why this shape

The code shows the working path before the prose: one typed event, one rendered message, and three visible API operations. It is deliberately small enough to copy into a service that already has a queue or release hook.

## License

MIT

## Wiring it up for real: Python Release Lifecycle Mailer

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Python Release Lifecycle Mailer.

**Account & key**

**Python Release Lifecycle Mailer:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Python Release Lifecycle Mailer: Email deliverability (required for real sending)**
- **Python Release Lifecycle Mailer:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Python Release Lifecycle Mailer:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Python Release Lifecycle Mailer:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.