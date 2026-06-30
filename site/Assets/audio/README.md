# Background music

Drop your track here as **`track.mp3`** (the path the site looks for is
`Assets/audio/track.mp3`, set in `Assets/js/shader-bg.js` as `AUDIO_SRC`).

Notes:
- **Use only music you own or are licensed to use.** A public portfolio is a
  public performance — don't post copyrighted tracks you don't have rights to.
  Royalty-free / Creative Commons or your own recording is the safe path.
- The player starts **paused** (browsers block autoplay with sound). Visitors
  press ▶ in the bottom-left "VIBE" control to start it.
- The shader background reacts to the audio (louder = bigger wave amplitude).
  With no file present, the visual still animates; it just won't pulse to sound.
- Keep the file reasonably small (a few MB) so the page stays fast; MP3 ~128–192
  kbps is plenty for ambient background.
