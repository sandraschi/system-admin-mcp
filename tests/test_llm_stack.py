"""Tests for the fleet LLM stack (providers, keystore, chat proxy, GPUs).

Keystore is isolated per-test via SYSTEMADMIN_LLM_KEYSTORE pointing at tmp_path.
Live-Ollama tests skip cleanly when no engine is reachable (CI-safe).
"""

import json
import os

import httpx
import pytest
from starlette.testclient import TestClient

from system_admin_mcp.server import app


@pytest.fixture
def keys_file(tmp_path, monkeypatch):
    path = tmp_path / "llm_keys.json"
    monkeypatch.setenv("SYSTEMADMIN_LLM_KEYSTORE", str(path))
    return path


@pytest.fixture
def client():
    return TestClient(app)


def _ollama_up() -> bool:
    try:
        r = httpx.get("http://127.0.0.1:11434/api/tags", timeout=3.0)
        return r.status_code == 200
    except Exception:
        return False


needs_ollama = pytest.mark.skipif(not _ollama_up(), reason="no local Ollama engine")


class TestProviders:
    def test_registry_shape(self, client):
        body = client.get("/api/llm/providers").json()
        assert isinstance(body["providers"], list)
        assert len(body["providers"]) >= 9
        ids = {p["id"] for p in body["providers"]}
        assert {"ollama", "openai", "anthropic", "meta", "google"} <= ids
        for p in body["providers"]:
            assert {"id", "label", "kind", "base_url", "needs_key", "key_env", "configured"} <= set(p)
            assert p["kind"] in ("local", "cloud")

    def test_no_key_bytes_leaked(self, client, keys_file):
        from system_admin_mcp import llm_providers as lp

        lp.save_key("openai", "sk-secret-xyz")
        body = client.get("/api/llm/providers").json()
        assert "sk-secret-xyz" not in json.dumps(body)
        settings = client.get("/api/settings/llm").json()
        assert "sk-secret-xyz" not in json.dumps(settings)
        assert settings["keys_configured"]["openai"] is True

    def test_models_curated_when_unkeyed(self, client, keys_file):
        body = client.get("/api/llm/models", params={"provider": "openai"}).json()
        assert body["source"] == "curated"
        assert body["key_missing"] is True
        assert len(body["models"]) >= 1

    def test_models_unknown_provider(self, client):
        body = client.get("/api/llm/models", params={"provider": "nope"}).json()
        assert body["source"] == "error"

    def test_endpoint_rejects_unknown(self, client):
        body = client.post("/api/llm/test", json={"provider": "nope"}).json()
        assert body["ok"] is False

    def test_endpoint_requires_provider(self, client):
        body = client.post("/api/llm/test", json={}).json()
        assert body["ok"] is False


class TestKeystore:
    def test_save_get_delete_roundtrip(self, client, keys_file):
        assert client.post("/api/settings/llm", json={"provider": "meta", "api_key": "  mk-test "}).json()["ok"] is True
        import stat

        mode = stat.S_IMODE(os.stat(keys_file).st_mode)
        assert mode == 0o600 or os.name == "nt"
        assert client.get("/api/settings/llm").json()["keys_configured"]["meta"] is True
        deleted = client.request("DELETE", "/api/settings/llm/key", params={"provider": "meta"}).json()
        assert deleted == {"ok": True, "deleted": True, "keys_configured": deleted["keys_configured"]}
        assert client.get("/api/settings/llm").json()["keys_configured"]["meta"] is False

    def test_save_rejects_local_provider(self, client, keys_file):
        body = client.post("/api/settings/llm", json={"provider": "ollama", "api_key": "x"}).json()
        assert body["ok"] is False

    def test_save_empty_key_is_noop(self, client, keys_file):
        body = client.post("/api/settings/llm", json={"provider": "openai", "api_key": "  "}).json()
        assert body["ok"] is True
        assert client.get("/api/settings/llm").json()["keys_configured"]["openai"] is False

    def test_delete_missing_key(self, client, keys_file):
        body = client.request("DELETE", "/api/settings/llm/key", params={"provider": "deepseek"}).json()
        assert body["ok"] is True and body["deleted"] is False

    def test_env_key_wins_without_keystore(self, client, keys_file, monkeypatch):
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-env-wins")
        assert client.get("/api/settings/llm").json()["keys_configured"]["deepseek"] is True


class TestChatContracts:
    def test_legacy_chat_requires_query(self, client):
        r = client.post("/api/chat", json={})
        assert r.status_code == 422

    def test_chat_validates_body(self, client):
        assert client.post("/api/llm/chat", json={}).json()["status"] == "error"
        body = client.post("/api/llm/chat", json={"provider": "ollama", "model": "", "messages": []}).json()
        assert body["status"] == "error"

    def test_chat_unknown_provider(self, client):
        body = client.post(
            "/api/llm/chat",
            json={"provider": "nope", "model": "x", "messages": [{"role": "user", "content": "hi"}]},
        ).json()
        assert body["status"] == "error"

    def test_chat_unkeyed_cloud_errors(self, client, keys_file, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        body = client.post(
            "/api/llm/chat",
            json={"provider": "openai", "model": "gpt-4o", "messages": [{"role": "user", "content": "hi"}]},
        ).json()
        assert body["status"] == "error" and "API key" in body["message"]

    @needs_ollama
    def test_chat_live_ollama(self, client):
        body = client.post(
            "/api/llm/chat",
            json={
                "provider": "ollama",
                "model": "gemma4:12b",
                "messages": [{"role": "user", "content": "Reply with exactly: live-ok"}],
            },
        ).json()
        assert body["status"] == "success" and "live-ok" in body["content"]

    @needs_ollama
    def test_stream_live_ollama(self, client):
        with client.stream(
            "POST",
            "/api/llm/chat/stream",
            json={
                "provider": "ollama",
                "model": "gemma4:12b",
                "messages": [{"role": "user", "content": "Reply with exactly: stream-live-ok"}],
            },
        ) as r:
            assert r.status_code == 200
            assert "text/event-stream" in r.headers["content-type"]
            text = ""
            for line in r.iter_lines():
                if line.startswith("data:"):
                    payload = line[5:].strip()
                    if payload and payload != "[DONE]":
                        obj = json.loads(payload)
                        text += obj.get("choices", [{}])[0].get("delta", {}).get("content", "")
        assert "stream-live-ok" in text


class TestGpuOnboardingInstall:
    def test_gpus_shape(self, client):
        body = client.get("/api/llm/gpus").json()
        assert isinstance(body["gpus"], list)
        for g in body["gpus"]:
            assert {"index", "name", "vramMb"} <= set(g)

    def test_ollama_state_shape(self, client):
        body = client.get("/api/llm/ollama/state").json()
        assert {"engine", "loaded", "installed"} <= set(body)

    def test_onboarding_shape(self, client, keys_file):
        body = client.get("/api/llm/onboarding").json()
        assert {"locals", "clouds_configured", "recommendation"} <= set(body)
        assert isinstance(body["locals"], list) and body["locals"]

    def test_install_rejects_unknown_engine(self, client):
        body = client.post("/api/llm/install", json={"engine": "nope"}).json()
        assert body["started"] is False

    def test_install_status_idle(self, client):
        body = client.get("/api/llm/install/status", params={"engine": "ollama"}).json()
        assert body["engine"] == "ollama" and body["state"] in ("idle", "running", "done", "error")
