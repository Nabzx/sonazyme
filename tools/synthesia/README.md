# Record Hana's scientist explanation

This tool records the supplied Hana Interactive Avatar delivering the
[reviewed script](../../docs/pitch/hana-script.md). It makes a prerecorded
MP4 for the existing video slot beside the simulation. It does not call an
LLM, improvise claims, record a user's microphone or change the simulation.

The rendering path uses the official Synthesia LiveKit plugin and Cartesia
through LiveKit Inference. The host's three LiveKit credentials cover the
room and voice. A Synthesia Interactive Avatar API key is also required for
this local renderer. Signing into Studio does not supply that key to the
renderer. An available connected Synthesia tool is a separate access path.

## Set up

Use an isolated environment so this does not change the core pipeline:

```bash
python3 -m venv .venv-avatar
source .venv-avatar/bin/activate
python -m pip install -r tools/synthesia/requirements.txt
npm install --prefix tools/synthesia
```

Google Chrome, ffmpeg and ffprobe must already be installed. The recorder uses
a fresh headless Chrome context. It does not inspect an existing browser
profile, cookies or logged-in account. Its private recording page captures
Hana's picture. A separate native LiveKit subscriber captures the rendered
voice used in the final MP4. Silent audio fails the output check. The API keys
stay in the Python process; only temporary room-scoped tokens reach that
private page, and they are never saved.

The repository's ignored `.env` needs these names:

```dotenv
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
SYNTHESIA_API_KEY=
```

`SYNTHESIA_API_URL` may be supplied if the hackathon host gave a special
endpoint. Otherwise the official plugin uses its own default. Hana's avatar
and voice ids come from the user's starter guide and are fixed in the tool.

## Check, then record

```bash
python tools/synthesia/record_hana.py --check
python tools/synthesia/record_hana.py
```

Check mode prints missing credential names, never values, and makes no network
or paid call. Recording creates a uniquely named Sonazyme room, starts Hana,
speaks the reviewed paragraphs, captures avatar audio and video, then deletes
its room. It times out rather than leaving an indefinite session running.
It refuses to overwrite an existing output or start without required keys.

Output files are:

- `web/media/scientist.mp4`: H.264/AAC video for offline playback.
- `web/media/scientist.vtt`: authored captions over observed speech intervals.
- `web/media/scientist.json`: public avatar/model ids, SDK versions, script and
  video hashes, generation time and measured media duration. No credentials.

Review the full clip before presenting: lip-sync, pronunciation, framing,
audibility and caption timing. The video is an AI presenter reading an
authored explanation. It is not a live scientist answer or experimental result.
Fine-tuning completion and improved stability are not claimed in the script.

## Access and references

- [Interactive Avatar concepts](https://developers.synthesia.io/docs/ia-concepts):
  the avatar is a live participant rather than a downloadable video job.
- [Official minimal quickstart](https://github.com/synthesia-ai/interactive-avatar-quickstarts/tree/main/minimal):
  plugin attachment and LiveKit session setup.
- [LiveKit agent speech](https://docs.livekit.io/agents/multimodality/audio/):
  fixed `session.say` speech without free-form generation.
- [Cartesia through LiveKit](https://docs.livekit.io/agents/models/tts/cartesia/):
  voice inference through the LiveKit project.

No video has been rendered until those output files exist and the renderer
has verified its audio and video streams. A missing connection or key must not
be presented as a completed recording.
