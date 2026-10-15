import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.lifecycle_mailer import BuildEvent, InfraiClient, publish_release


def main() -> None:
    recipient = os.environ.get("RELEASE_NOTICE_TO")
    if not recipient:
        raise SystemExit("RELEASE_NOTICE_TO is required")
    event = BuildEvent(
        release_tag=os.environ.get("RELEASE_TAG", "v0.1.0"),
        succeeded=os.environ.get("BUILD_OK", "1") == "1",
        diagnostics=os.environ.get("BUILD_DIAGNOSTICS", "All checks passed"),
    )
    result = publish_release(InfraiClient(), event, recipient)
    print("release notice sent", result)


if __name__ == "__main__":
    main()
