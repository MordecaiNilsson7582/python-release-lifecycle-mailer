from src.lifecycle_mailer import BuildEvent, InfraiClient, compose_release_mail, publish_release


def test_failed_build_is_explicit_in_subject_and_body():
    mail = compose_release_mail(BuildEvent("v2.4.0", False, "type check failed"))
    assert mail.subject == "Release v2.4.0: needs attention"
    assert "type check failed" in mail.html


def test_template_requests_follow_discovery_contract(monkeypatch):
    calls = []
    monkeypatch.setattr(InfraiClient, "_request", lambda self, method, path, payload: calls.append((method, path, payload)))
    client = InfraiClient(api_key="test")
    client.create_template("release", "Subject", "<p>Hello</p>")
    client.preview_template("template-1", {"release_tag": "v1"})
    assert calls == [
        ("POST", "/v1/email/template/create", {
            "name": "release", "subject": "Subject", "html": "<p>Hello</p>",
            "variables": ["release_tag", "diagnostics"],
        }),
        ("POST", "/v1/email/template/preview/template-1", {"vars": {"release_tag": "v1"}}),
    ]


def test_publish_previews_created_template():
    class Client:
        def create_template(self, *args):
            return {"template_id": "template-1"}

        def preview_template(self, template_id, variables):
            assert template_id == "template-1"
            assert variables["release_tag"] == "v1"

        def send_email(self, *args):
            return {"sent": True}

    assert publish_release(Client(), BuildEvent("v1", True, "ok"), "chenhua@changba.com") == {"sent": True}
