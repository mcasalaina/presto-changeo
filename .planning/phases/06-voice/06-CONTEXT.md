# Phase 6: Voice - Context

**Gathered:** 2026-01-18
**Status:** Ready for research

<vision>
## How This Should Work

When voice is enabled, it's a hands-free experience — just start talking, no button presses needed. Toggle it on and the system is always listening, like talking to Alexa or Siri. The AI responds both vocally and visually, creating a natural conversational flow.

There's a mute button visible when voice is active. Pressing mute suppresses mic input to prevent the AI from hearing itself (feedback loops), but the gpt-realtime model stays connected and functional. Unmute and you're right back to talking.

The interaction should feel like talking to a person, not issuing commands. When the AI says "here's your spending for March," the chart appears at that moment — voice and visuals in sync.

</vision>

<essential>
## What Must Be Nailed

- **Natural conversation flow** - It should feel like talking to a person, not a command system
- **Voice-visual synchronization** - When AI says "here's your chart," the chart appears at that exact moment
- **Clean audio handling** - No feedback loops, smooth voice detection, seamless transitions between listening and speaking

All three are equally important — they work together to create the experience.

</essential>

<specifics>
## Specific Ideas

- Minimal visual indicator when listening/speaking — subtle pulse or waveform, nothing distracting
- Mute button suppresses mic input but keeps gpt-realtime model connected
- Always-listening when voice toggle is enabled (no wake word)

</specifics>

<notes>
## Additional Context

The mute functionality is specifically designed to prevent the AI from interfering with itself — when the AI speaks, the mic could pick it up and create feedback. The user wants the ability to suppress input while keeping the voice session active.

</notes>

---

*Phase: 06-voice*
*Context gathered: 2026-01-18*
