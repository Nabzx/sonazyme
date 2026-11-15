"""Launch the read-only run API, or export and restore verified offline snapshots."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sonazyme.api.server import Application, make_server
from sonazyme.api.snapshots import export_snapshot, read_snapshot, restore_snapshot

DEFAULT_STRUCTURE_DIRECTORY = Path(__file__).resolve().parents[3] / "assets" / "structures"


def main(argv: list[str] | None = None) -> None:
    """Serve local data without running models or publishing a hosted site."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments and arguments[0] in {"export", "restore"}:
        action = arguments[0]
        parser = argparse.ArgumentParser(description=f"{action.capitalize()} a saved run snapshot")
        parser.add_argument("--run-dir", type=Path, required=True)
        parser.add_argument(
            "--output" if action == "export" else "--snapshot", type=Path, required=True
        )
        args = parser.parse_args(arguments[1:])
        try:
            if action == "export":
                snapshot = export_snapshot(args.run_dir)
                # Refuse to overwrite an existing file or accidentally replace a manifest.
                with args.output.open("x", encoding="utf-8") as stream:
                    json.dump(snapshot, stream, allow_nan=False)
                    stream.write("\n")
            else:
                restore_snapshot(read_snapshot(args.snapshot), args.run_dir)
        except (OSError, ValueError) as error:
            parser.exit(2, f"{action.capitalize()} failed: {error}\n")
        print(f"Snapshot {action} complete. No new inference was run.")
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    parser.add_argument("--web-dir", type=Path)
    parser.add_argument("--structures-dir", type=Path, default=DEFAULT_STRUCTURE_DIRECTORY)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args(arguments)
    if args.web_dir is not None and not (args.web_dir / "index.html").is_file():
        parser.exit(
            2, "Optional dashboard files not found at --web-dir. Omit it for API-only mode.\n"
        )
    try:
        server = make_server(
            Application(
                args.runs_dir,
                args.web_dir,
                structure_directory=args.structures_dir,
            ),
            args.port,
        )
    except (OSError, OverflowError) as error:
        parser.exit(2, f"Cannot start API: {error}\n")
    print(f"Sonazyme API: http://127.0.0.1:{server.server_port}", flush=True)
    print("Saved run inspection only. No model calls or experimental results.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
