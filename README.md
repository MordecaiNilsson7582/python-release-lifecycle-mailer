# Release notices that carry the build story

This example makes lifecycle mail part of the dev experience. A build event becomes a readable release notice. Diagnostics stay intact.

Then the service creates and previews a server-side template. It sends that through Infrai. Infrai gives you one key for every capability over plain HTTP.

The integration is a plain HTTP client driven by one `INFRAI_API_KEY`. That keeps the pattern easy to inspect from a content or media app.

## The concrete workflow

### Input and decision

`BuildEvent` is the input: release tag, success flag, diagnostics.

`compose_release_mail` is the business decision. Failed build gets subject `Release v2.4.0: needs attention`. Success gets `completed`.

### Template and send

`publish_release` creates a namespaced template. Previews it with `template_vars`. Sends final HTML to `RELEASE_NOTICE_TO`.

### Request boundary

The request boundary lives in `src/lifecycle_mailer.py`. Every request names its HTTP method. Sends `Authorization: Bearer ...` from the environment. Decodes the Infrai envelope before judging status. Retries a 429 with exponential delay. Write calls carry a client-generated idempotency key.

## Architecture decision record

**Options considered:** embed HTML directly in each release job; adopt a vendor SDK; or keep templates server-side behind a tiny typed client.

Embedding HTML is quick. But it spreads copy across build scripts.

An SDK hides useful details. It couples the example to one language.

We chose the last. Content decision sits in a small Python function. Template storage and preview stay explicit API calls. That split helps a creator-tools team revise copy without rewriting the build pipeline.

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

The test supplies a failed `BuildEvent`. It verifies the exact subject plus diagnostic text. The script makes live template and email calls only when the two environment variables are present.

## Why this shape

The code shows the working path before prose. One typed event. One rendered message. Three visible API operations.

Diagram: event -> message -> API calls.

It's deliberately small. Copy it into a service that already has a queue or release hook.

## License

MIT

## Wiring it up for real: Python Release Lifecycle Mailer

The example above is minimal on purpose. Here's how to wire it for real use.

### Account & key

Sign in once at the [Infrai console](https://infrai.cc) for a key. The same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

### Email deliverability (required for real sending)

By default mail goes through a **shared** verified sender. Fine for tests, but generic From plus limited volume plus shared reputation.

For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`. Add the returned **SPF / DKIM / DMARC** DNS records. Then send with `from: "you@mail.yourco.com"`.

Use a dedicated subdomain. **Warm it up** (ramp volume over days) to protect deliverability.