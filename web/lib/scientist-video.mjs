// Load only a completed recording. A missing or failed clip keeps the placeholder.
async function loadScientistVideo() {
  const frame = document.querySelector('.talk__frame');
  if (!frame || frame.querySelector('video')) return;
  try {
    const response = await fetch('media/scientist.json');
    if (!response.ok) return;
    const production = await response.json();
    if (production.kind !== 'recorded-scientist-video' ||
        production.avatar_id !== '3190429b-1eda-4151-bf24-96162e405840') return;

    const video = document.createElement('video');
    video.className = 'talk__video';
    video.controls = true;
    video.playsInline = true;
    video.preload = 'metadata';
    video.setAttribute('aria-label', 'Hana explains Sonazyme. AI presenter; no wet-lab result.');
    const captions = document.createElement('track');
    captions.kind = 'captions';
    captions.src = 'media/scientist.vtt';
    captions.srclang = 'en-GB';
    captions.label = 'English';
    captions.default = true;
    video.append(captions);
    video.addEventListener('loadedmetadata', () => {
      if (video.videoWidth > 0 && video.duration > 0) frame.prepend(video);
    }, { once: true });
    video.addEventListener('error', () => video.remove());
    video.src = 'media/scientist.mp4';
  } catch {
    // A static preview or absent recording must still display a usable page.
  }
}

loadScientistVideo();
