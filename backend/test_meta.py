import hashlib
import hmac
import json

import config
import meta


def test_signature():
    config.META_APP_SECRET = "s3cret"
    body = b'{"a":1}'
    good = "sha256=" + hmac.new(b"s3cret", body, hashlib.sha256).hexdigest()
    assert meta.verify_signature(body, good)
    assert not meta.verify_signature(body, "sha256=00")
    assert not meta.verify_signature(body, "")


def test_owner_gets_reply_others_only_stored(monkeypatch):
    stored, sent = [], []
    monkeypatch.setattr(meta, "_store", lambda *a: stored.append(a))
    monkeypatch.setattr(meta, "send_whatsapp_text", lambda to, text: sent.append((to, text)))
    monkeypatch.setattr(meta.orchestrator, "chat", lambda sid, text: f"ответ на {text}")
    config.OWNER_WHATSAPP = "+7 701 123 45 67"
    payload = {"entry": [{"changes": [{"value": {"messages": [
        {"from": "77011234567", "id": "a", "type": "text", "text": {"body": "сколько заказов?"}},
        {"from": "77770000000", "id": "b", "type": "text", "text": {"body": "здравствуйте"}},
    ]}}]}]}
    assert meta.handle(payload) == {"handled": 2}
    assert len(stored) == 2
    assert sent == [("77011234567", "ответ на сколько заказов?")]


def test_instagram_dm_is_stored_not_answered(monkeypatch):
    stored, sent = [], []
    monkeypatch.setattr(meta, "_store", lambda *a: stored.append(a))
    monkeypatch.setattr(meta, "send_whatsapp_text", lambda to, text: sent.append(to))
    payload = {"object": "instagram", "entry": [{"messaging": [
        {"sender": {"id": "123"}, "message": {"mid": "m1", "text": "Сколько стоит подушка?"}},
        {"sender": {"id": "999"}, "message": {"mid": "m2", "text": "эхо", "is_echo": True}},
    ]}]}
    assert meta.handle(payload) == {"handled": 1}
    assert stored[0][:3] == ("instagram", "123", "Сколько стоит подушка?")
    assert sent == []


def test_signature_with_instagram_secret():
    config.META_APP_SECRET = ""
    config.INSTAGRAM_APP_SECRET = "igsecret"
    body = b'{"object":"instagram"}'
    good = "sha256=" + hmac.new(b"igsecret", body, hashlib.sha256).hexdigest()
    assert meta.verify_signature(body, good)
