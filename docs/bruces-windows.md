# Bruce's Windows

**Source:** `WINDOW1.png`
**Mode:** Functionally interactive (exception to the automated-only rule; this is the reference for the shared UI chrome)

## What it shows

Windows 3.1-style chrome: a title bar reading "Window Title," a "Dialog" box titled "Welcome to Bruce's Windows" with a "Got it" button, and a status bar reading "This is a status bar...".

## Behaviour

Renders the window and dialog on load. No auto-looping animation.

## Interaction

- Title bar is draggable.
- "Got it" button closes the dialog.

## Assets

Custom-drawn chrome to match `WINDOW1.png`. May double as the reference implementation for the shared UI framework (README priority 2), though that work is tracked separately.

## Open questions

- Scope of interactivity beyond drag and "Got it" (e.g. a working close/minimize box, whether the dialog is modal) is unspecified. Treat drag + "Got it" as the baseline.
