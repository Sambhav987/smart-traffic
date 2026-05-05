import os
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from core.models import PushToken  # adjust import to your app

# Initialize the Firebase Admin SDK exactly once per process.
if not firebase_admin._apps:
    cred_path = getattr(settings, "FIREBASE_CREDENTIALS_PATH", None) \
        or os.environ.get("FIREBASE_CREDENTIALS_PATH")
    if not cred_path:
        raise RuntimeError(
            "Set FIREBASE_CREDENTIALS_PATH (in settings.py or env) to the "
            "Firebase service account JSON file."
        )
    firebase_admin.initialize_app(credentials.Certificate(cred_path))


def send_push(title, body, data=None):
    """Send an FCM push to every registered device. Prunes invalid tokens."""
    tokens = list(PushToken.objects.values_list("token", flat=True))
    if not tokens:
        print("[push] no tokens registered")
        return

    # FCM data payloads must be string-to-string.
    data_payload = {k: str(v) for k, v in (data or {}).items()}

    message = messaging.MulticastMessage(
        tokens=tokens,
        notification=messaging.Notification(title=title, body=body),
        data=data_payload,
        android=messaging.AndroidConfig(priority="high"),
    )
    response = messaging.send_each_for_multicast(message)
    print(f"[push] sent: success={response.success_count} failure={response.failure_count}")

    # Clean up tokens FCM rejected as no-longer-valid.
    for token, resp in zip(tokens, response.responses):
        if not resp.success:
            err = resp.exception
            code = getattr(err, "code", "") or ""
            if code in ("registration-token-not-registered", "invalid-argument"):
                PushToken.objects.filter(token=token).delete()
                print(f"[push] removed invalid token: {token[:20]}…")
            else:
                print(f"[push] error for {token[:20]}…: {err}")
