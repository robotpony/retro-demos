# CD Player

**Source:** `CDPLAYER.png`
**Mode:** Automated attract-mode

## What it shows

CD player chrome: numeric LED time/track readout, transport buttons (play/pause/stop/skip/eject), a vertical slider bank, and green dot-matrix level meters.

## Behaviour

Simulated playback only, no real audio. The time counter increments on its own, the level meters animate with a fake waveform, and transport buttons visually indicate state (e.g. "play" shown as pressed) without triggering real audio.

## Interaction

None beyond the shared quit/pause controls.

## Assets

No existing sprite sheet; chrome is custom-drawn to match `CDPLAYER.png`.

## Notes

No real audio files are bundled or played, by design.
