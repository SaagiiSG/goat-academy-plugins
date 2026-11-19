---
name: mn-voice
description: Make character voice lines with ElevenLabs Eleven v4, tuned for Mongolian (respelling tricks for з and р, emotion tags, takes, timing for lip sync). Use for voice lines, narration or dialogue in an animation, especially in Mongolian, or when a Mongolian TTS line sounds rough or wrong.
allowed-tools: Bash(python3 *), Bash(python *), Bash(ffmpeg *), Bash(ffprobe *)
---

# Voices (ElevenLabs v4, Mongolian first)

`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/voice.py say "[calm, warm] TEXT" VOICE_ID voice/line.mp3 --lang mn`

It prints the length. Needs `ELEVENLABS_API_KEY`. Eleven v4 only works through the text-to-dialogue endpoint, which
`say` uses. Leave `--lang` off for English and other languages.

## Voices that worked
Stock ElevenLabs voices. Never clone a real person's voice without their written OK.

| Voice | ID | Used for |
|---|---|---|
| Bill | `pqHfZKP75CvOlQylNhV4` | Old, wise, warm narrator (Чингис хаан) |
| Liam | `TX3LPaxmHKxFdv7VOQHJ` | Young business owner |
| Brian | `nPczCjzI2devNBz1zQrb` | Deep, confident coach |
| Chris | `iP95p4xoKVk53GoZ742B` | Casual, energetic founder |
| Eric | `cjVigY5qzO86Huf0OWal` | Calm, polished executive |

More: the ElevenLabs Voice Library on their website (copy the voice ID from there).

## Making a line
- Start with a tag that sets the mood: `[calm, wise]`, `[tired]`, `[warm]`, `[proud, warm]`, `[sighs]`. Keep it calm;
  big emotion tags make v4 overact. When a line sounded "too emotional", a calmer tag fixed it.
- Make **2–3 takes** of every line (`voice/test/a.mp3`, `b.mp3` …) and let the user pick by ear. Takes differ in
  length and stress.
- Run at most 3 requests at once (the plan's limit); more fail.
- The length sets the shot. For lip sync, keep the line just under a whole second (billing is per whole second):
  `voice.py fit voice/a.mp3 voice/a-fit.mp3 2.95` trims the end. To shorten the middle, cut a pause, but never speed the
  voice up.
- `voice.py pauses FILE` lists the gaps, for caption timing and cut points.

## Mongolian: what v4 gets wrong and how to fix it
v4 says Mongolian **з** like a Russian "z" and doesn't roll **р**, so lines sound rough. Respell the text you send,
but keep the real spelling in the captions.

| Problem | Fix that worked | Note |
|---|---|---|
| з sounds like "z" | write **дз**: "зар" → "дзар", "зардал" → "дзардал", "зохион" → "дзохион" | Fixed most words. "захиалга" stayed wrong even respelled, so it was swapped for another word ("хүргэлт") |
| р not rolled | write **рр**: "морьтон" → "моррьтон", "бүрдүүл" → "бүррдүүл", "өрсөлдөгч" → "өррсөлдөгч" | Judge word by word. "бичээррэй" came out too hard, so the single р stayed |
| English words in the line | keep them in Latin: "AI", "GOAT" | A Latin brand word reads better than a Cyrillic respelling, but the user chooses by ear |
| An English name sounds like another word | say it in Mongolian ("AI Team 28 Challenge" sounded like "AI teens", so the line became "Хорин найман хоногийн AI челленж") | |

If respelling isn't enough: record the line yourself and run it through ElevenLabs speech-to-speech into the chosen
voice (not tested yet).

## Before any video
Put the voices over the still frames in a free animatic (reel-edit skill, stills as cuts) and let the user listen.
Voices are cheap to redo, but lip-synced video is not, and a voice change after lip sync means redoing the lip sync.
