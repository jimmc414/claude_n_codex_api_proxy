import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import setup_proxy  # noqa: E402


def _prepare_home(monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(setup_proxy.Path, "home", lambda: home)
    return home


def test_generate_certificates_waits_for_ca(monkeypatch, tmp_path, capsys):
    home = _prepare_home(monkeypatch, tmp_path)
    cert_dir = home / ".mitmproxy"
    ca_cert = cert_dir / "mitmproxy-ca-cert.pem"

    current_time = {"value": 0.0}

    def fake_monotonic():
        return current_time["value"]

    def fake_sleep(duration):
        if not ca_cert.exists():
            cert_dir.mkdir(parents=True, exist_ok=True)
            ca_cert.write_text("cert")
        current_time["value"] += duration

    monkeypatch.setattr(setup_proxy.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(setup_proxy.time, "sleep", fake_sleep)

    class DummyProc:
        def __init__(self):
            self.terminated = False
            self.wait_called = False
            self.killed = False

        def poll(self):
            return 0 if self.terminated else None

        def terminate(self):
            assert ca_cert.exists(), "terminate called before certificate exists"
            self.terminated = True

        def wait(self, timeout=None):
            assert self.terminated, "wait called before terminate"
            self.wait_called = True
            return 0

        def kill(self):
            self.killed = True

    proc_holder = {}

    def fake_popen(*args, **kwargs):
        proc = DummyProc()
        proc_holder["proc"] = proc
        return proc

    monkeypatch.setattr(setup_proxy.subprocess, "Popen", fake_popen)

    returned_dir = setup_proxy.generate_certificates()

    proc = proc_holder["proc"]
    assert returned_dir == cert_dir
    assert ca_cert.exists()
    assert proc.terminated
    assert proc.wait_called
    assert not proc.killed

    captured = capsys.readouterr().out
    assert f"CA certificate generated at {ca_cert}" in captured


def test_generate_certificates_warns_on_timeout(monkeypatch, tmp_path, capsys):
    home = _prepare_home(monkeypatch, tmp_path)
    cert_dir = home / ".mitmproxy"
    ca_cert = cert_dir / "mitmproxy-ca-cert.pem"

    current_time = {"value": 0.0}

    def fake_monotonic():
        return current_time["value"]

    def fake_sleep(duration):
        current_time["value"] += duration

    monkeypatch.setattr(setup_proxy.time, "monotonic", fake_monotonic)
    monkeypatch.setattr(setup_proxy.time, "sleep", fake_sleep)

    class DummyProc:
        def __init__(self):
            self.terminated = False
            self.wait_called = False
            self.killed = False

        def poll(self):
            return 0 if self.terminated else None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            assert self.terminated, "wait called before terminate"
            self.wait_called = True
            return 0

        def kill(self):
            self.killed = True

    proc_holder = {}

    def fake_popen(*args, **kwargs):
        proc = DummyProc()
        proc_holder["proc"] = proc
        return proc

    monkeypatch.setattr(setup_proxy.subprocess, "Popen", fake_popen)

    returned_dir = setup_proxy.generate_certificates()

    proc = proc_holder["proc"]
    assert returned_dir == cert_dir
    assert not ca_cert.exists()
    assert proc.terminated
    assert proc.wait_called

    captured = capsys.readouterr().out
    assert "timed out waiting for mitmdump" in captured
    assert "CA certificate generated" not in captured
    assert "Run 'mitmdump' once manually" in captured
