# ADR-0014: Record Hana delivering an evidence-linked scientist explanation

- Status: Accepted
- Date: 2026-11-15
- Issues: #61, #95

## Context

The user wants a prerecorded Synthesia Hana video beside the enzyme simulation.
The hackathon guide provides a real-time Interactive Avatar over LiveKit,
not a rendered video download endpoint. The video must replay offline and
must describe actual computational work without claiming physical production,
lab testing or completed fine-tuning that the run does not contain.

## Decision

Author a fixed GCSE-level narration with a claim ledger, using the source
artefacts and biology documentation already in the repo. Use Hana's supplied
avatar and Cartesia voice ids. Synthesia supplies the face; LiveKit Inference
supplies the voice. No LLM writes or improvises the recorded speech. This is an
authored explanation, not a live answer from the run's explain stage.

Use an isolated optional recording toolchain: the official Synthesia LiveKit
plugin, LiveKit Agents, python-dotenv and Playwright. The recorder captures
avatar video in the browser and decoded room audio through LiveKit's native
SDK, then uses ffmpeg to produce a local MP4. Silent audio fails the recording
check. SDK and encoding versions are kept in production metadata. This adds
no dependency to the core pipeline.

Keys remain in `.env` or process environment. Do not print keys, room tokens,
provider error bodies or authenticated URLs. Check all required credentials
before creating a room or making a paid call. A connected Synthesia tool can
replace API recording if it is available; a browser login alone is not assumed
to expose API credentials. The recorder creates only its own named room and
cleans up that room after recording or failure.

The completed clip is `web/media/scientist.mp4`, with captions and a public
production record. The UI identifies Hana as an AI presenter. Source claims
are reviewed before speech synthesis. Do not create a broken video element
or hide the placeholder until a real recorded video is available. Existing
colours and the partner's simulation stay outside this change.

Once the recording exists, embed it directly in the right-hand video slot
with a still from the clip as its poster and native playback controls.
Displaying the player must not depend on a detached video element loading
metadata or a JavaScript request succeeding. Serve byte ranges for the MP4
so browser media probes and seeking work locally.

The website's existing notice carries the experimental status beside the
video. At the user's request, the narration does not repeat that notice.
It describes computational designs and predictions without implying physical
production or measured activity.

## Consequences

The demo can play Hana's explanation without conference networking. The script
can be revised when the partner supplies new evidence, then recorded again.
An absent Synthesia connection/key blocks rendering, not script preparation.
Model confidence, unchanged sequence positions and geometry are not described
as experimental activity or verified stability in a loop.

## Alternatives considered

A live avatar would add network and interaction risk to the pitch. A free-form
LLM narration could introduce unsupported claims. A stock talking-head video
would not preserve the user's requested Hana identity. These are rejected.
