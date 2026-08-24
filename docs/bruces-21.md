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
