# Dooley

**Source:** `DOOLEY1.png`
**Mode:** Automated attract-mode

## What it shows

LED-style display with a column of colour pixels down the left edge alongside a main LED display area.

## Behaviour

Combines both: scrolling text moves across the main display while the colour-pixel column cycles through a colour pattern alongside it.

## Interaction

None beyond the shared quit/pause controls.

## Assets

Shares rendering primitives with the LED framework (see `led.md`, `led-ii.md`, `title.md`).

## Open questions

- Whether the colour-pixel cycling should react to the scrolling text's content, or run independently, is unspecified. Treat as independent unless told otherwise.
