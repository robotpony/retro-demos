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

Custom-drawn chrome to match `WINDOW1.png`. Per `PLAN.md`, this chrome is not extracted into the shared framework; CD Player and Tank Status Window draw their own window-style borders independently.

## Open questions

- Scope of interactivity beyond drag and "Got it" (e.g. a working close/minimize box, whether the dialog is modal) is unspecified. Treat drag + "Got it" as the baseline.
- This demo's role is expected to grow: see `PLAN.md`'s "Future: the unified desktop (end state)" section (logged 2026-08-24) -- Bruce's Windows' chrome becomes the desktop shell that every other demo eventually runs inside, as its own window, rather than staying a single title-bar-plus-dialog demo forever. Not scheduled yet; every other demo needs to be built first.
