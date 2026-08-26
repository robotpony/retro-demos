# Bruce's 21

**Source:** `CARDS.png`, `BACKS.png`
**Mode:** Automated attract-mode

## What it shows

Full 52-card face deck (A-K, four suits) from `CARDS.png`, plus two "Bruce's 21" card-back designs from `BACKS.png`.

## Behaviour

Loops between two phases automatically:

1. **Deck cycle:** shuffles and flips through the full face deck and both card backs, showing off the sprite art.
2. **Auto-deal:** deals and reveals hands as if playing a round of 21, without real blackjack scoring or win logic. Visual only.

## Interaction

None beyond the shared quit/pause controls (interface framework, README priority 2).

## Assets

`CARDS.png` (deck sprite sheet), `BACKS.png` (2 back designs).

## Notes

The name implies blackjack, but this demo does not implement real game rules or scoring.

**Build (2026-08-25):** `CARDS.png`'s 14th column isn't card art -- it's leftover splash/credit art from the original program (a title card, a portrait, a logo, a blank), out of scope for this build. Unlike every other demo, this one loads `CARDS.png`/`BACKS.png` at runtime instead of hand-encoding pixel data (confirmed with Bruce: 52 detailed card faces is too much to transcribe by hand). Built as a demo, not a game (Bruce's explicit call): the auto-deal script produces a plausible-looking dealer/player hand with a hole-card reveal and an occasional "hit," but never computes a hand value. See `retrodemos/demos/bruces_21.py`'s module docstring for the full account.

**Playtesting (2026-08-26):** three real fixes. Card backs cycled at their raw 64x82 size instead of the 48x66 size every card and hand slot uses, so the deck-cycle phase visibly jumped size twice a lap -- now always shown at slot size (`Deck.back_for_slot`). Every card/back sprite has a 3px rounded-corner "L" notch filled with a flat background grey in the source ((192,192,192) for cards, (198,198,198) for backs) that isn't part of the art; blitting the tile as-is put that grey square over the felt instead of a rounded corner, so it's now punched fully transparent (measured identically across a dozen sampled cards, position-based rather than colour-based). The table itself grew and dropped its card overlap entirely: this deck's own art isn't corner-indexed like a real playing card (a small rank+suit mark tucked in one corner) -- it's one giant rank glyph filling most of the card with the suit pip only in the corners -- so any real fan overlap hid the rank behind the next card. Cards now sit edge to edge.
