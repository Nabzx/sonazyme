"""Check read-only run access, offline replay and incremental saved-manifest events."""

import base64
import json
import threading
from copy import deepcopy
from http.client import HTTPConnection

import pytest

from sonazyme.api.__main__ import main
from sonazyme.api.server import Application, make_server
from sonazyme.api.snapshots import export_snapshot, restore_snapshot
from sonazyme.core.manifest import append, create, finish
from sonazyme.runs.store import RunStore


@pytest.fixture
def saved(tmp_path):
    root = tmp_path / "runs"
    store = RunStore(root / "one")
    target = store.put(b"software fixture input; no biological values")
    store.save(create("fixture-run", target))
    return root, store, Application(root)


def attempt():
    return {
        "id": "sense-fixture",
        "stage": "sense",
        "status": "succeeded",
        "producer": {"name": "software-fixture", "version": "1", "kind": "code"},
        "inputs": [],
        "parameters": {},
        "metrics": [],
        "artefacts": [],
        "reason": None,
    }


def decoded(response):
    return json.loads(response.body)


def test_api_starts_without_any_dashboard_files(saved):
    _, store, app = saved
    assert decoded(app.get("/"))["service"] == "sonazyme.api"
    assert app.get("/api/health").status == 200
    listed = decoded(app.get("/api/runs"))
    assert listed["runs"][0]["key"] == "one"
    assert listed["runs"][0]["run_id"] == "fixture-run"
    assert "file_modified_at" in listed["runs"][0]
    assert decoded(app.get("/api/runs/one/manifest")) == store.load()
    assert app.get("/styles.css").status == 404


def test_only_referenced_artefacts_can_be_read(saved):
    _, store, app = saved
    ref = store.load()["target"]
    response = app.get(f"/api/runs/one/artefacts/{ref['sha256']}")
    assert response.status == 200
    assert response.body == store.read(ref)
    assert response.content_type == "application/octet-stream"
    orphan = store.put(b"not referenced")
    assert app.get(f"/api/runs/one/artefacts/{orphan['sha256']}").status == 404
    assert orphan["sha256"] not in decoded(app.get("/api/runs/one/snapshot"))["artefacts"]


@pytest.mark.parametrize(
    "path",
    [
        "/.env",
        "/.git/config",
        "/../pyproject.toml",
        "/%2e%2e/.env",
        "/api/runs/%2e%2e/manifest",
        "/api/runs/one/artefacts/../../.env",
        "/api/runs/one/artefacts/%2fetc%2fpasswd",
        "/api/runs/%00/manifest",
    ],
)
def test_traversal_and_repository_files_are_not_served(saved, path):
    assert saved[2].get(path).status == 404


def test_missing_and_corrupt_runs_are_distinguished(saved, tmp_path):
    root, store, app = saved
    assert app.get("/api/runs/missing/manifest").status == 404
    target = store.load()["target"]
    (store.directory / target["path"]).unlink()
    assert app.get("/api/runs/one/manifest").status == 409
    listing = decoded(app.get("/api/runs"))
    assert listing["runs"] == []
    assert listing["unavailable"] == [{"key": "one", "reason": "Snapshot or artefacts unavailable"}]
    store.manifest_path.write_text("not json")
    assert app.get("/api/runs/one/manifest").status == 409
    assert decoded(Application(tmp_path / "absent").get("/api/runs"))["runs"] == []


def test_symlink_escapes_are_rejected(saved, tmp_path):
    root, store, app = saved
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "manifest.json").write_text("private fixture")
    (root / "escape").symlink_to(outside)
    assert app.get("/api/runs/escape/manifest").status == 404
    manifest = store.load()
    target_path = store.directory / manifest["target"]["path"]
    target_path.unlink()
    target_path.symlink_to(outside / "manifest.json")
    assert app.get("/api/runs/one/manifest").status == 409


def test_optional_static_root_is_allowlisted(saved, tmp_path):
    web = tmp_path / "not-a-real-website"
    web.mkdir()
    (web / "index.html").write_text("static transport fixture")
    (web / ".env").write_text("not served")
    app = Application(saved[0], web)
    assert app.get("/").body == b"static transport fixture"
    assert app.get("/.env").status == 404
    (web / "styles.css").symlink_to(web.parent / "outside.css")
    (web.parent / "outside.css").write_text("not served")
    assert app.get("/styles.css").status == 404


def test_snapshot_round_trip_preserves_sealed_manifest_and_bytes(saved, tmp_path):
    _, store, _ = saved
    store.save(finish(append(store.load(), attempt())))
    snapshot = export_snapshot(store.directory)
    expected = store.load()
    destination = tmp_path / "replayed"
    restore_snapshot(snapshot, destination)
    replay = RunStore(destination)
    assert replay.load() == expected
    assert replay.read(expected["target"]) == store.read(expected["target"])
    assert replay.load()["status"] == "finished"
    assert "not a model run date" in snapshot["metadata"]["notice"]
    with pytest.raises(FileExistsError):
        restore_snapshot(snapshot, destination)


@pytest.mark.parametrize("damage", ["digest", "encoding", "missing", "extra", "schema"])
def test_invalid_snapshot_does_not_publish_a_run(saved, tmp_path, damage):
    _, store, _ = saved
    snapshot = deepcopy(export_snapshot(store.directory))
    digest = snapshot["manifest"]["target"]["sha256"]
    if damage == "digest":
        raw = base64.b64decode(snapshot["artefacts"][digest])
        snapshot["artefacts"][digest] = base64.b64encode(b"X" * len(raw)).decode()
    elif damage == "encoding":
        snapshot["artefacts"][digest] = "!"
    elif damage == "missing":
        snapshot["artefacts"].clear()
    elif damage == "extra":
        snapshot["artefacts"]["0" * 64] = ""
    else:
        snapshot["manifest"]["schema_version"] = 100
    destination = tmp_path / "invalid-copy"
    with pytest.raises(ValueError):
        restore_snapshot(snapshot, destination)
    assert not destination.exists()
    assert store.load()["run_id"] == "fixture-run"


def test_export_and_restore_size_limits(saved, tmp_path, monkeypatch):
    import sonazyme.api.snapshots as snapshots

    snapshot = export_snapshot(saved[1].directory)
    monkeypatch.setattr(snapshots, "MAX_EXPORT_BYTES", 1)
    with pytest.raises(ValueError, match="size limit"):
        export_snapshot(saved[1].directory)
    with pytest.raises(ValueError, match="size limit"):
        restore_snapshot(snapshot, tmp_path / "too-large")
    assert not (tmp_path / "too-large").exists()


def test_export_restore_cli_refuses_overwrites_and_never_calls_a_model(saved, tmp_path, capsys):
    _, store, _ = saved
    output = tmp_path / "snapshot.json"
    main(["export", "--run-dir", str(store.directory), "--output", str(output)])
    original = output.read_bytes()
    with pytest.raises(SystemExit) as raised:
        main(["export", "--run-dir", str(store.directory), "--output", str(output)])
    assert raised.value.code == 2
    assert output.read_bytes() == original
    restored = tmp_path / "restored"
    main(["restore", "--snapshot", str(output), "--run-dir", str(restored)])
    assert RunStore(restored).load() == store.load()
    assert "No new inference was run" in capsys.readouterr().out


def test_events_follow_saved_appends_and_stop_when_sealed(saved):
    _, store, app = saved

    def update():
        store.save(finish(append(store.load(), attempt())))

    events = app.events("one", wait=update)
    first = next(events)
    second = next(events)
    assert b"event: manifest" in first and b"event: manifest" in second
    assert first != second
    assert json.loads(second.decode().split("data: ")[1])["entries"][0]["id"] == "sense-fixture"
    assert b"event: end" in next(events)
    with pytest.raises(StopIteration):
        next(events)


def test_event_reconnection_skips_an_unchanged_manifest(saved):
    _, _, app = saved
    first_stream = app.events("one", wait=lambda: None)
    first = next(first_stream).decode()
    identity = first.split("id: ")[1].splitlines()[0]
    first_stream.close()
    reconnected = app.events("one", last_event_id=identity, wait=lambda: None)
    assert next(reconnected).startswith(b": saved run unchanged")
    reconnected.close()


def test_events_end_with_error_instead_of_sending_corrupt_data(saved):
    _, store, app = saved

    def corrupt():
        store.manifest_path.write_text("private invalid fixture")

    stream = app.events("one", wait=corrupt)
    assert b"event: manifest" in next(stream)
    error = next(stream)
    assert b"event: error" in error and b"private" not in error
    with pytest.raises(StopIteration):
        next(stream)


def test_video_media_probes_and_seeking_use_byte_ranges(saved, tmp_path):
    root, _, _ = saved
    web = tmp_path / "web"
    (web / "media").mkdir(parents=True)
    (web / "media/scientist.mp4").write_bytes(b"0123456789")
    server = make_server(Application(root, web), port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        cases = [
            ("bytes=0-1", 206, b"01", "bytes 0-1/10"),
            ("bytes=7-", 206, b"789", "bytes 7-9/10"),
            ("bytes=-3", 206, b"789", "bytes 7-9/10"),
            ("bytes=8-99", 206, b"89", "bytes 8-9/10"),
            ("bytes=10-", 416, b"", "bytes */10"),
            ("bytes=4-2", 416, b"", "bytes */10"),
            ("bytes=-0", 416, b"", "bytes */10"),
            ("bytes=0-1,4-5", 200, b"0123456789", None),
        ]
        for header, status, body, content_range in cases:
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request("GET", "/media/scientist.mp4", headers={"Range": header})
            response = connection.getresponse()
            assert response.status == status
            assert response.getheader("Accept-Ranges") == "bytes"
            assert response.getheader("Content-Range") == content_range
            assert int(response.getheader("Content-Length")) == len(body)
            assert response.read() == body
            connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_http_transport_read_only_host_checks_and_sse(saved):
    _, store, app = saved
    store.save(finish(store.load()))
    before = store.manifest_path.read_bytes()
    server = make_server(app, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request("GET", "/api/health")
        response = connection.getresponse()
        assert response.status == 200
        assert response.getheader("X-Content-Type-Options") == "nosniff"
        response.read()
        connection.close()
        for method in ("POST", "PUT", "PATCH", "DELETE"):
            connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
            connection.request(method, "/api/runs/one/manifest", body=b"ignored")
            response = connection.getresponse()
            assert response.status == 405 and response.getheader("Allow") == "GET"
            response.read()
            connection.close()
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request("GET", "/api/runs", headers={"Host": "unrelated.example"})
        response = connection.getresponse()
        assert response.status == 403
        response.read()
        connection.close()
        connection = HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request("GET", "/api/runs/one/events")
        response = connection.getresponse()
        assert response.status == 200 and response.getheader("Content-Type").startswith(
            "text/event-stream"
        )
        body = response.read()
        assert b"event: manifest" in body and b"event: end" in body
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert store.manifest_path.read_bytes() == before
