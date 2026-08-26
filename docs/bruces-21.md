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
