"""Record a fixed, reviewed Hana narration and encode a reusable MP4.

No LLM call is made. Credentials are loaded privately from the repository's
.env file. --check performs no network or paid operation.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import threading
import wave
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
TOOL = Path(__file__).resolve().parent
AVATAR_ID = "3190429b-1eda-4151-bf24-96162e405840"
VOICE_ID = "1ac31ebd-9113-405b-9d80-4a4bbbeea91c"
TTS_MODEL = "cartesia/sonic-3.6-2026-08-27"
REQUIRED_ENV = ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "SYNTHESIA_API_KEY")


def narration(path: Path) -> list[str]:
    """Extract only the reviewed spoken section, never notes or citations."""
    text = path.read_text(encoding="utf-8")
    if "## Spoken script\n\n" not in text or "\n## Delivery notes" not in text:
        raise ValueError("Script needs Spoken script and Delivery notes sections")
    spoken = text.split("## Spoken script\n\n", 1)[1].split("\n## Delivery notes", 1)[0]
    paragraphs = [" ".join(part.split()) for part in spoken.strip().split("\n\n") if part.strip()]
    if not paragraphs or sum(len(p.split()) for p in paragraphs) > 600:
        raise ValueError("Narration is empty or exceeds the recording length limit")
    return paragraphs


def spoken_text(text: str) -> str:
    """Use pronunciation spellings only for speech, keeping display text intact."""
    return (
        text.replace("NucB", "Nuke Bee")
        .replace("DNase", "DNA-cutting enzyme")
        .replace("MutRank", "Mute Rank")
        .replace("Hyper M P N N", "Hyper, M, P, N, N")
    )


def vtt_time(seconds: float) -> str:
    """Format a non-negative recording timestamp as WebVTT time."""
    milliseconds = max(0, round(seconds * 1000))
    seconds, ms = divmod(milliseconds, 1000)
    minutes, sec = divmod(seconds, 60)
    hours, minute = divmod(minutes, 60)
    return f"{hours:02}:{minute:02}:{sec:02}.{ms:03}"


def captions(segments: list[dict]) -> str:
    """Split authored text into readable cues within observed speech intervals."""
    cues = ["WEBVTT", ""]
    for segment in segments:
        words = segment["text"].split()
        groups = [words[i : i + 12] for i in range(0, len(words), 12)]
        duration = max(0.1, segment["end"] - segment["start"])
        consumed = 0
        for group in groups:
            start = segment["start"] + duration * consumed / len(words)
            consumed += len(group)
            end = segment["start"] + duration * consumed / len(words)
            cues.extend([f"{vtt_time(start)} --> {vtt_time(end)}", " ".join(group), ""])
    return "\n".join(cues)


def recorder_server(bundle: Path) -> ThreadingHTTPServer:
    """Serve just the temporary recording page and the pinned browser SDK."""
    files = {
        "/": (TOOL / "recorder.html", "text/html"),
        "/livekit-client.umd.js": (bundle, "text/javascript"),
    }

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            """Return no credentials and expose no generic filesystem route."""
            if self.path not in files:
                self.send_error(404)
                return
            path, content_type = files[self.path]
            data = path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format, *args):
            """Keep tokens and authenticated URLs out of logs."""

    return ThreadingHTTPServer(("127.0.0.1", 0), Handler)


async def record(paragraphs: list[str], destination: Path, bundle: Path) -> list[dict]:
    """Create a private-purpose room and record only Hana's rendered tracks."""
    from livekit import api, rtc
    from livekit.agents import Agent, AgentSession, inference, room_io
    from livekit.plugins import synthesia
    from playwright.async_api import async_playwright

    room_name = f"sonazyme-hana-{uuid4().hex}"
    avatar_identity = "sonazyme-hana"
    client = api.LiveKitAPI()
    room = rtc.Room()
    audio_room = rtc.Room()
    audio_tasks = []
    audio_streams = []
    audio_packets = {}
    audio_peaks = {}
    loop = asyncio.get_running_loop()
    recording_started = None
    recording_stopped = None

    async def receive_audio(track, key):
        stream = rtc.AudioStream(track, sample_rate=48000, num_channels=1)
        audio_streams.append(stream)
        audio_packets[key] = []
        audio_peaks[key] = 0
        async for event in stream:
            if recording_started is not None:
                frame = event.frame
                audio_packets[key].append((loop.time(), bytes(frame.data)))
                audio_peaks[key] = max(audio_peaks[key], max(map(abs, frame.data), default=0))

    @audio_room.on("track_subscribed")
    def subscribed(track, publication, participant):
        if track.kind == rtc.TrackKind.KIND_AUDIO and participant.identity in {
            avatar_identity,
            "sonazyme-narrator",
        }:
            key = (participant.identity, publication.sid)
            audio_tasks.append(asyncio.create_task(receive_audio(track, key)))

    session = None
    avatar = None
    created = False
    segments = []
    server = recorder_server(bundle)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def token(identity: str, publish: bool) -> str:
        return (
            api.AccessToken()
            .with_identity(identity)
            .with_ttl(timedelta(minutes=15))
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=room_name,
                    can_publish=publish,
                    can_subscribe=True,
                    can_publish_data=publish,
                )
            )
            .to_jwt()
        )

    try:
        await client.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=60,
                departure_timeout=20,
                sync_streams=True,
            )
        )
        created = True
        print("Recording room created; connecting Hana", flush=True)
        await room.connect(os.environ["LIVEKIT_URL"], token("sonazyme-narrator", True))
        await audio_room.connect(os.environ["LIVEKIT_URL"], token("sonazyme-audio-recorder", False))
        session = AgentSession(
            tts=inference.TTS(
                model=TTS_MODEL, voice=VOICE_ID, language="en", extra_kwargs={"speed": 1.02}
            ),
            turn_handling={"preemptive_generation": {"enabled": False}},
        )
        avatar = synthesia.AvatarSession(
            synthesia.AvatarConfig(avatar_ids=[AVATAR_ID]),
            join_timeout=60,
            avatar_participant_identity=avatar_identity,
            avatar_participant_name="Hana",
        )
        await avatar.start(session, room=room)
        print("Hana connected; starting reviewed narration", flush=True)
        await session.start(
            agent=Agent(
                instructions="Read only the supplied reviewed narration. Do not improvise."
            ),
            room=room,
            room_options=room_io.RoomOptions(
                audio_input=False,
                video_input=False,
                text_input=False,
                text_output=False,
                close_on_disconnect=False,
            ),
        )
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(
                channel="chrome",
                headless=True,
                args=["--autoplay-policy=no-user-gesture-required"],
            )
            try:
                page = await browser.new_page()
                with destination.open("wb") as output:

                    async def write_chunk(encoded: str) -> None:
                        output.write(base64.b64decode(encoded, validate=True))

                    await page.expose_function("writeRecordingChunk", write_chunk)
                    await page.goto(f"http://127.0.0.1:{server.server_port}/")
                    await page.evaluate(
                        "window.connectAvatar",
                        {
                            "url": os.environ["LIVEKIT_URL"],
                            "token": token("sonazyme-recorder", False),
                            "identity": avatar_identity,
                        },
                    )
                    await page.wait_for_function(
                        "document.getElementById('preview').videoWidth > 0",
                        timeout=90000,
                    )
                    recording_started = loop.time()
                    await page.evaluate("window.startRecording()")
                    await asyncio.sleep(0.5)
                    for index, text in enumerate(paragraphs, 1):
                        if await page.evaluate("window.recordingError"):
                            raise RuntimeError("Avatar recording failed")
                        start = await page.evaluate("window.recordingTime()")
                        await session.say(spoken_text(text), allow_interruptions=False)
                        if not audio_peaks or max(audio_peaks.values()) < 33:
                            raise ValueError("No audible avatar speech was received")
                        end = await page.evaluate("window.recordingTime()")
                        segments.append({"text": text, "start": start, "end": end})
                        print(f"Recorded narration segment {index}/{len(paragraphs)}", flush=True)
                        await asyncio.sleep(0.3)
                    await asyncio.sleep(2)
                    await page.evaluate("window.stopRecording()")
                    recording_stopped = loop.time()
                    await page.evaluate("window.closeRecordingRoom()")
            finally:
                await browser.close()
    finally:
        for stream in audio_streams:
            await stream.aclose()
        for task in audio_tasks:
            task.cancel()
        await asyncio.gather(*audio_tasks, return_exceptions=True)
        await audio_room.disconnect()
        for resource in (session, avatar):
            if resource is not None:
                try:
                    await resource.aclose()
                except Exception:
                    pass
        await room.disconnect()
        if created:
            try:
                await client.room.delete_room(api.DeleteRoomRequest(room=room_name))
            except Exception:
                print("Room cleanup was not confirmed; check the Sonazyme Hana room in LiveKit.")
        await client.aclose()
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    if recording_started is None or recording_stopped is None or not audio_peaks:
        raise ValueError("Native audio recording did not complete")
    chosen = max(audio_peaks, key=audio_peaks.get)
    pcm = bytearray(round((recording_stopped - recording_started) * 48000) * 2)
    previous_end = None
    for received, data in audio_packets[chosen]:
        # Keep contiguous samples together; align real pauses to the video clock.
        offset = max(0, round((received - recording_started) * 48000) - len(data) // 2) * 2
        if previous_end is not None and abs(offset - previous_end) < 9600:
            offset = previous_end
        end = min(len(pcm), offset + len(data))
        if end > offset:
            pcm[offset:end] = data[: end - offset]
            previous_end = end
    with wave.open(str(destination.with_suffix(".wav")), "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(48000)
        audio.writeframes(pcm)
    return segments


def encode(source: Path, output: Path, audio_source: Path | None = None) -> dict:
    """Produce an offline H.264/AAC MP4 and inspect its actual streams."""
    subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-v",
            "error",
            "-i",
            str(source),
            *(
                ["-i", str(audio_source), "-map", "0:v:0", "-map", "1:a:0", "-shortest"]
                if audio_source is not None
                else []
            ),
            "-vf",
            "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
            "-c:v",
            "libx264",
            "-preset",
            "medium",
            "-crf",
            "20",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(output),
        ],
        check=True,
        capture_output=True,
    )
    report = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    metadata = json.loads(report.stdout)
    if not {"video", "audio"}.issubset({stream["codec_type"] for stream in metadata["streams"]}):
        raise ValueError("Recording is missing its audio or video stream")
    if float(metadata["format"]["duration"]) <= 1:
        raise ValueError("Recording is empty")
    volume = subprocess.run(
        ["ffmpeg", "-nostdin", "-i", str(output), "-vn", "-af", "volumedetect", "-f", "null", "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    peak = re.search(r"max_volume: ([\-\w.]+) dB", volume.stderr)
    if peak is None or float(peak[1]) < -60:
        raise ValueError("Recorded audio is silent or too quiet")
    return metadata


def main(argv: list[str] | None = None) -> None:
    """Validate prerequisites before any paid operation, then record one take."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--script", type=Path, default=ROOT / "docs/pitch/hana-script.md")
    parser.add_argument("--output", type=Path, default=ROOT / "web/media/scientist.mp4")
    args = parser.parse_args(argv)
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env", override=False)
    paragraphs = narration(args.script)
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name, "").strip()]
    bundle = TOOL / "node_modules/livekit-client/dist/livekit-client.umd.js"
    print(f"Reviewed script: {sum(len(p.split()) for p in paragraphs)} words; presenter: Hana")
    print("Missing credentials: " + (", ".join(missing) if missing else "none"))
    print(
        "Browser SDK: "
        + ("installed" if bundle.is_file() else "run npm install in tools/synthesia")
    )
    if args.check:
        return
    if missing:
        parser.exit(2, "Recording not started. Add the missing credentials to .env.\n")
    if not bundle.is_file() or not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        parser.exit(2, "Recording not started. Install the browser SDK and ffmpeg/ffprobe first.\n")
    if args.output.exists():
        parser.exit(2, "Output already exists. Choose a new --output path for another take.\n")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Provider exception bodies and SDK logs must not leak credentials to the terminal.
    logging.basicConfig(level=logging.CRITICAL, force=True)

    async def bounded_record(raw: Path) -> list[dict]:
        from livekit.agents.utils import http_context

        async with asyncio.timeout(600):
            async with http_context.open():
                return await record(paragraphs, raw, bundle)

    try:
        with tempfile.TemporaryDirectory(prefix="sonazyme-hana-") as temporary:
            raw = Path(temporary) / "hana.webm"
            segments = asyncio.run(bounded_record(raw))
            encoded = Path(temporary) / "hana.mp4"
            media = encode(raw, encoded, raw.with_suffix(".wav"))
            args.output.with_suffix(".vtt").write_text(captions(segments), encoding="utf-8")
            shutil.copyfile(encoded, args.output)
        production = {
            "schema_version": 1,
            "kind": "recorded-scientist-video",
            "presenter": "Hana",
            "avatar_id": AVATAR_ID,
            "voice_id": VOICE_ID,
            "tts_model": TTS_MODEL,
            "created_at": datetime.now(UTC).isoformat(),
            "script_sha256": hashlib.sha256(args.script.read_bytes()).hexdigest(),
            "video_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
            "duration_seconds": float(media["format"]["duration"]),
            "sdk_versions": {
                name: version(name)
                for name in ("livekit-agents", "livekit-plugins-synthesia", "playwright")
            },
            "browser_sdk_version": json.loads((TOOL / "package-lock.json").read_text())["packages"][
                "node_modules/livekit-client"
            ]["version"],
            "ffmpeg_version": subprocess.run(
                ["ffmpeg", "-version"], check=True, capture_output=True, text=True
            ).stdout.splitlines()[0],
            "notice": (
                "AI presenter delivering an authored explanation. No Sonazyme wet-lab result."
            ),
            "caption_timing": (
                "Cues distributed over observed speech intervals; review before presenting"
            ),
        }
        args.output.with_suffix(".json").write_text(json.dumps(production, indent=2) + "\n")
        print(f"Hana video recorded: {args.output}")
    except Exception as error:
        diagnostic = type(error).__name__
        if diagnostic == "SynthesiaError":
            from livekit.plugins.synthesia.errors import ErrorType

            category = getattr(error, "type", None)
            if isinstance(category, ErrorType):
                diagnostic += f": {category.value}"
            status = getattr(error, "status", None)
            if isinstance(status, int):
                diagnostic += f"; HTTP {status}"
        parser.exit(2, f"Recording failed ({diagnostic}). Provider details withheld.\n")


if __name__ == "__main__":
    main()
