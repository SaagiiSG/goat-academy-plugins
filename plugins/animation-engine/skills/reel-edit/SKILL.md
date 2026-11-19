---
name: reel-edit
description: Cut a vertical reel from shots, stills and voice lines with frame-exact cuts, stepped "on 2s" motion, lower-third captions and hand-drawn comic graphics (comic words, stickers, spinning-head icons, speed lines, impact bursts, phone notifications, counters, end cards). Use for the edit step of an animation, a free animatic from still frames, or adding comic graphics and captions to any footage.
allowed-tools: Bash(python3 *), Bash(python *), Bash(ffmpeg *), Bash(ffprobe *)
---

# Reel edit

`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/reel.py render timeline.json out.mp4 --stills`

It builds a 1080×1920, 24 fps MP4 with loudness at −16 LUFS. `--stills` saves one frame from the middle of each cut
into `out-check/`. Read them every time. Paths in the timeline are relative to the timeline file.

## Timeline format
```json
{
  "cuts": [
    {"start": 0.00, "end": 1.20, "src": "shots/owner-talk.mp4", "sync": 0.00},
    {"start": 1.20, "end": 2.08, "src": "shots/ads.mp4", "in": 0.3, "on": 2},
    {"start": 2.08, "end": 3.95, "src": "shots/owner-talk.mp4", "sync": 0.00},
    {"start": 3.95, "end": 6.00, "src": "frames/end.png"}
  ],
  "voices": [{"at": 0.00, "file": "voice/o1.mp3"}],
  "music": {"file": "music/bed.mp3", "db": -20},
  "captions": [
    {"start": 0.10, "end": 1.20, "text": "Контент,"},
    {"start": 1.20, "end": 3.95, "text": "бүгдийг ганцаараа."}
  ],
  "graphics": [
    {"type": "comic", "text": "?!", "x": 800, "y": 520, "size": 220, "start": 1.8, "end": 2.9}
  ]
}
```

**Cuts** play back to back. Each `end` is the next `start`, and the last `end` is the reel's length.
- `src`: a video or a still (PNG/JPG). A reel made only of stills is a free **animatic**.
- `in`: where in the clip to start (seconds, default 0).
- `sync`: the timeline time where the clip's 0 s sits. Use it for lip-sync clips. Give every cut of the same talking
  clip the same `sync` as its voice's `at`, and you can cut away to other shots and back with the mouth still matched.
- `on`: `2` holds every pose 2 frames (comic-book feel), `3` holds 3 (paper-cut, stop-motion). Use it on action
  shots and cutaways. Keep talking shots smooth (`1`, the default).

**Voices** start at `at` seconds. Lip-sync clips are muted; their voice file goes here at the same time as the clip's
`sync`. `db` changes one voice's level. **Music** loops under everything at `db` (default −18).

**Captions**: plain white with a soft shadow, centred, in the lower third (y 1290). They wrap inside x 120–960. One
short phrase at a time, timed to the words (`voice.py pauses FILE` shows where the breaks are). Set `"y"` on a
caption to move it, e.g. to the top when the lower third would cover a talking mouth. Write the real spelling
here even if the voice line was respelled for the TTS.

**Graphics**: every type takes `start`, `end`, and `pop` (when it pops in; default `start`). Sizes and positions are
in pixels on the 1080×1920 frame. They're drawn at 12 fps with a slight hand-drawn jitter.

| type | fields | what it is |
|---|---|---|
| `comic` | `text, x, y, size`, optional `count: [from, to]` with `{n}` in the text | Yellow comic word, ink outline, offset magenta/cyan plates. `count` rolls the number up over 0.35 s ("DAY {n}") |
| `sprite` | `image, x, y, size`, optional `rot` | A transparent PNG sticker (icon, prop, emoji-like drawing) |
| `dizzy` | `x, y` (centre above the head), `images: [...]`, optional `rx, ry, size` | Motion arcs plus icons orbiting a head: stress, overwhelm, "my head is spinning" |
| `speedlines` | optional `x, y` | Zoom lines rushing to the centre, for dives, rushes and reveals |
| `burst` | optional `x, y` | Two frames of impact lines at `start`, for an entrance or a hit |
| `card` | `lines: [small, big], y` | A drawn phone notification with a green tick ("AI worker · now" / "2 posts published") |
| `text` | `text, y`, optional `size` (36) | Small plain white text, e.g. a disclaimer or a subtitle line |
| `image` | `image`, optional `fade` (s) | A full-frame transparent PNG, e.g. an end card |

Keep `x` within 120–960 and `y` within 270–1248. Phone apps put buttons on the right edge and the caption at the
bottom, and reel.py warns when something sits outside. Fonts are Fira Sans (Cyrillic and Mongolian included). Swap them
with `"fonts": {"comic": "...ttf", "caption": "...ttf", "text": "...ttf"}`.

## Stickers
Make a sheet of transparent icons in one call (`gpt-image-2-5-flare-text-to-image` with `background: "transparent"` and `resolution: "1K"` (transparency only works at 1K),
6 credits; check fields with `kie.py schema`). Ask for "a 4×2 grid of separate flat comic sticker icons with thick
black ink outlines, evenly spaced, nothing touching". Then
`reel.py split sheet.png 4x2 camera,megaphone,chat,box,bulb,drop,star,bolt sprites/` gives one PNG each.

## How to cut it
1. Get each line's length (`voice.py length`) and its pauses (`voice.py pauses`). Lay the voices on the timeline
   first, with 0.1–0.25 s of air between lines.
2. Cut on the words: change the picture every 0.8–1.5 s in lists and action, and hold 2–3 s on a talking face.
3. Lip-sync clip: one cut per sentence with `sync` set. Cutaways in between show what's being said (they say "army",
   we see the army).
4. Graphics show the feeling (stress, an idea, speed) or a number. Don't decorate every shot.
5. End: hold the last shot 2–3 s past the call to action, with the end title drawn as `comic` + `text`.
6. Render with `--stills`, read every check frame, fix, render again. Rendering takes about 1–2 minutes for 30 s.
