"""A loopback-only, read-only run API and static dashboard server."""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

from sonazyme.api.snapshots import export_snapshot, modified_at, references
from sonazyme.runs.store import RunStore

JS = "text/javascript; charset=utf-8"
STATIC_FILES = {
    "index.html": "text/html; charset=utf-8",
    "styles.css": "text/css; charset=utf-8",
    "tokens.css": "text/css; charset=utf-8",
    "app.mjs": JS,
    "lib/api.mjs": JS,
    "lib/data.mjs": JS,
    "lib/viewer.mjs": JS,
    "lib/protein.mjs": JS,
    "lib/film.mjs": JS,
    "lib/pipe.mjs": JS,
    "lib/sonar.mjs": JS,
    "lib/overhead.mjs": JS,
    "lib/scroll.mjs": JS,
    "lib/tokens.mjs": JS,
    "media/scientist.jpg": "image/jpeg",
    "media/scientist.mp4": "video/mp4",
    "media/scientist.vtt": "text/vtt; charset=utf-8",
    "media/scientist.json": "application/json; charset=utf-8",
    "lib/structures.mjs": JS,
    "vendor/three.module.js": JS,
    "vendor/3Dmol-min.js": JS,
    "data/enzyme.json": "application/json; charset=utf-8",
    "enzyme.png": "image/png",
    "fonts/instrument-serif-400.woff2": "font/woff2",
    "fonts/geist-400.woff2": "font/woff2",
    "fonts/geist-500.woff2": "font/woff2",
    "fonts/geist-mono-400.woff2": "font/woff2",
}
LOCAL_STRUCTURE_FORMATS = {
    ".cif": "cif",
    ".ent": "pdb",
    ".mmcif": "cif",
    ".pdb": "pdb",
}

SECURITY_HEADERS = {
    "Cache-Control": "no-store",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "font-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; object-src 'none'; "
        "base-uri 'none'; frame-ancestors 'none'"
    ),
}


@dataclass
class Response:
    """Transport a response independently of the HTTP listener."""

    status: int
    body: bytes
    content_type: str = "application/json; charset=utf-8"
    filename: str | None = None


@dataclass(frozen=True)
class LocalStructure:
    """Describe one allowlisted structure file from the local model folder."""

    identity: str
    group: str
    name: str
    format: str
    path: Path
    size_bytes: int


def _json(value: object, status: int = 200, filename: str | None = None) -> Response:
    return Response(status, (json.dumps(value, allow_nan=False) + "\n").encode(), filename=filename)


class Application:
    """Expose saved files through a small, explicit set of read-only routes."""

    def __init__(
        self,
        runs_directory: Path,
        web_directory: Path | None = None,
        *,
        structure_directory: Path | None = None,
    ):
        """Select the run, web and local structure roots."""
        self.runs_directory = runs_directory.resolve()
        self.web_directory = web_directory.resolve() if web_directory is not None else None
        self.structure_directory = (
            structure_directory.resolve() if structure_directory is not None else None
        )

    def _local_structures(self) -> list[LocalStructure]:
        root = self.structure_directory
        if root is None or not root.is_dir():
            raise FileNotFoundError("The configured local structure directory is unavailable")

        structures = []
        for path in root.rglob("*"):
            if path.is_symlink() or not path.is_file():
                continue
            structure_format = LOCAL_STRUCTURE_FORMATS.get(path.suffix.lower())
            if structure_format is None:
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to(root):
                continue
            relative = path.relative_to(root)
            group = (
                "Root models"
                if len(relative.parts) == 1 or relative.parts[0] == "predictions"
                else relative.parts[0]
            )
            name = (
                Path(*relative.parts[1:]).as_posix()
                if group != "Root models" and len(relative.parts) > 1
                else relative.as_posix()
            )
            structures.append(
                LocalStructure(
                    identity=hashlib.sha256(relative.as_posix().encode("utf-8")).hexdigest(),
                    group=group,
                    name=name,
                    format=structure_format,
                    path=resolved,
                    size_bytes=resolved.stat().st_size,
                )
            )
        return sorted(
            structures,
            key=lambda item: (
                item.group != "Root models",
                item.group.casefold(),
                item.name.casefold(),
            ),
        )

    def _local_structure_groups(self) -> list[dict[str, object]]:
        groups: dict[str, list[dict[str, object]]] = {}
        for structure in self._local_structures():
            groups.setdefault(structure.group, []).append(
                {
                    "id": structure.identity,
                    "name": structure.name,
                    "format": structure.format,
                    "size_bytes": structure.size_bytes,
                }
            )
        return [{"name": name, "structures": structures} for name, structures in groups.items()]

    def _directory(self, key: str) -> Path:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", key) or key in {".", ".."}:
            raise FileNotFoundError("Unknown run")
        directory = self.runs_directory / key
        if directory.is_symlink() or not directory.resolve().is_relative_to(self.runs_directory):
            raise FileNotFoundError("Unknown run")
        if not (directory / "manifest.json").is_file():
            raise FileNotFoundError("Unknown run")
        if (directory / "manifest.json").is_symlink():
            raise ValueError("Manifest symlinks are not served")
        return directory

    def _list(self) -> dict:
        runs, unavailable = [], []
        if not self.runs_directory.exists():
            return {"runs": runs, "unavailable": unavailable}
        for path in sorted(self.runs_directory.iterdir()):
            if not path.is_dir() or path.name.startswith("."):
                continue
            try:
                directory = self._directory(path.name)
                store = RunStore(directory)
                manifest = store.load()
                runs.append(
                    {
                        "key": path.name,
                        "run_id": manifest["run_id"],
                        "status": manifest["status"],
                        "file_modified_at": modified_at(store.manifest_path),
                    }
                )
            except (OSError, ValueError, TypeError, KeyError):
                unavailable.append(
                    {"key": path.name, "reason": "Snapshot or artefacts unavailable"}
                )
        runs.sort(key=lambda run: run["file_modified_at"], reverse=True)
        return {"runs": runs, "unavailable": unavailable}

    def get(self, request_path: str) -> Response:
        """Serve a verified manifest or referenced artefact, never an arbitrary path."""
        path = unquote(urlsplit(request_path).path)
        parts = path.strip("/").split("/")
        try:
            if path == "/api/health":
                return _json({"status": "ok", "service": "sonazyme.api", "version": "1"})
            if path == "/local-structures.json":
                try:
                    return _json({"groups": self._local_structure_groups()})
                except (FileNotFoundError, OSError):
                    return _json(
                        {"error": "The configured local structure directory is unavailable"},
                        503,
                    )
            if len(parts) == 2 and parts[0] == "local-structures":
                identity = parts[1]
                if not re.fullmatch(r"[0-9a-f]{64}", identity):
                    return _json({"error": "Unknown local structure"}, 404)
                try:
                    structure = next(
                        (item for item in self._local_structures() if item.identity == identity),
                        None,
                    )
                    if structure is None:
                        return _json({"error": "Unknown local structure"}, 404)
                    return Response(
                        200,
                        structure.path.read_bytes(),
                        "text/plain; charset=utf-8",
                    )
                except (FileNotFoundError, OSError):
                    return _json({"error": "The selected local structure is unavailable"}, 503)
            if path == "/" and self.web_directory is None:
                return _json(
                    {
                        "service": "sonazyme.api",
                        "version": "1",
                        "routes": [
                            "/api/health",
                            "/api/runs",
                            "/api/runs/<key>/manifest",
                            "/api/runs/<key>/artefacts/<sha256>",
                            "/api/runs/<key>/snapshot",
                            "/api/runs/<key>/events",
                        ],
                        "notice": (
                            "Read-only saved run API. No model calls or experimental results."
                        ),
                    }
                )
            if path == "/api/runs":
                return _json(self._list())
            if len(parts) >= 3 and parts[:2] == ["api", "runs"]:
                store = RunStore(self._directory(parts[2]))
                try:
                    manifest = store.load()
                except (OSError, ValueError, TypeError, KeyError):
                    return _json(
                        {"error": "Snapshot cannot be verified; check its manifest and artefacts"},
                        409,
                    )
                if len(parts) == 4 and parts[3] == "manifest":
                    return _json(manifest)
                if len(parts) == 4 and parts[3] == "snapshot":
                    return _json(
                        export_snapshot(store.directory), filename="sonazyme-snapshot.json"
                    )
                if (
                    len(parts) == 5
                    and parts[3] == "artefacts"
                    and re.fullmatch(r"[0-9a-f]{64}", parts[4])
                ):
                    ref = references(manifest).get(parts[4])
                    if ref is not None:
                        return Response(200, store.read(ref), "application/octet-stream", parts[4])
                return _json({"error": "Not found"}, 404)
            static = "index.html" if path == "/" else path.lstrip("/")
            if self.web_directory is not None and static in STATIC_FILES:
                file = self.web_directory / static
                if file.is_symlink() or not file.resolve().is_relative_to(self.web_directory):
                    return _json({"error": "Not found"}, 404)
                return Response(200, file.read_bytes(), STATIC_FILES[static])
            return _json({"error": "Not found"}, 404)
        except FileNotFoundError:
            return _json({"error": "Not found"}, 404)
        except (OSError, ValueError, TypeError, KeyError):
            return _json(
                {"error": "Snapshot cannot be verified; check its manifest and artefacts"}, 409
            )

    def events(
        self,
        key: str,
        last_event_id: str | None = None,
        wait: Callable[[], None] = lambda: time.sleep(1),
    ) -> Iterator[bytes]:
        """Stream verified saved manifests, with reconnection ids and comment heartbeats."""
        previous = last_event_id
        while True:
            try:
                manifest = RunStore(self._directory(key)).load()
                data = json.dumps(manifest, sort_keys=True, allow_nan=False)
                identity = hashlib.sha256(data.encode()).hexdigest()
            except (OSError, ValueError, TypeError, KeyError):
                yield b'event: error\ndata: {"error":"Saved run cannot be verified"}\n\n'
                return
            if identity != previous:
                yield f"event: manifest\nid: {identity}\ndata: {data}\n\n".encode()
                previous = identity
            else:
                yield b": saved run unchanged\n\n"
            if manifest["status"] == "finished":
                yield b'event: end\ndata: {"status":"finished"}\n\n'
                return
            wait()


def make_server(application: Application, port: int = 8000) -> ThreadingHTTPServer:
    """Bind the development server to loopback, with no mutation handlers."""

    class Handler(BaseHTTPRequestHandler):
        def _respond(self, response: Response) -> None:
            status, body = response.status, response.body
            media = status == 200 and response.content_type == "video/mp4"
            content_range = None
            if media:
                size = len(body)
                requested = re.fullmatch(
                    r"bytes=(\d{0,20})-(\d{0,20})", self.headers.get("Range", "")
                )
                if requested and any(requested.groups()):
                    first, last = requested.groups()
                    start = int(first) if first else max(0, size - int(last))
                    end = min(int(last), size - 1) if first and last else size - 1
                    if start >= size or end < start:
                        status, body = 416, b""
                        content_range = f"bytes */{size}"
                    else:
                        status, body = 206, body[start : end + 1]
                        content_range = f"bytes {start}-{end}/{size}"
            self.send_response(status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(body)))
            if media:
                self.send_header("Accept-Ranges", "bytes")
            if content_range is not None:
                self.send_header("Content-Range", content_range)
            if response.status == 405:
                self.send_header("Allow", "GET")
            for name, value in SECURITY_HEADERS.items():
                self.send_header(name, value)
            if response.filename:
                self.send_header(
                    "Content-Disposition", f'attachment; filename="{response.filename}"'
                )
            self.end_headers()
            try:
                self.wfile.write(body)
            except (BrokenPipeError, ConnectionResetError):
                # A media client may stop downloading after reading metadata.
                pass

        def do_GET(self):
            """Reject non-local hosts and dispatch an allowlisted read route."""
            host = self.headers.get("Host", "").split(":")[0]
            if host not in {"127.0.0.1", "localhost"}:
                self._respond(_json({"error": "Local access only"}, 403))
                return
            parts = unquote(urlsplit(self.path).path).strip("/").split("/")
            if len(parts) == 4 and parts[:2] == ["api", "runs"] and parts[3] == "events":
                check = application.get(f"/api/runs/{parts[2]}/manifest")
                if check.status != 200:
                    self._respond(check)
                    return
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Connection", "close")
                for name, value in SECURITY_HEADERS.items():
                    self.send_header(name, value)
                self.end_headers()
                try:
                    for event in application.events(parts[2], self.headers.get("Last-Event-ID")):
                        self.wfile.write(event)
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    return
            else:
                self._respond(application.get(self.path))

        def do_POST(self):
            """Reject writes rather than invoking or mutating a stage."""
            self._respond(_json({"error": "This service is read-only"}, 405))

        do_PUT = do_POST
        do_PATCH = do_POST
        do_DELETE = do_POST

        def log_message(self, format, *args):
            """Keep local requests quiet and omit query strings from logs."""

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
