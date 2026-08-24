# Cinqtris

**Source:** `CT_ANI.png`, `CT_PRTS.png`
**Mode:** Automated attract-mode, with one interactive control

## What it shows

Title screen with three cells across the top: a "CINQTRIS" wordmark, a 10-segment "equalizer," and a "MADMAX" cell (Bruce's old handle).

## Behaviour

- The wordmark animates across the three title cells on a loop.
- The 10-segment equalizer cycles its columns through a defined set of patterns on a loop. Exact patterns are an implementation detail, not specified further here.

## Interaction

The "MADMAX" cell is a button. Activating it opens an About popup (credits/info). This is the one interactive element in an otherwise automated demo.

## Assets

`CT_PRTS.png` supplies the colour/gem palette and bitmap font used for the title text and equalizer segments, and the button-state sprites (normal/hover/pressed) for the MADMAX button.

## Open questions

- Exact equalizer animation patterns (random bar heights vs. a fixed sequence) are unspecified; pick a reasonable default during implementation.
