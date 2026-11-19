# GOAT Academy plugins for Claude Code

Two plugins for making short AI animations with Claude Code, [kie.ai](https://kie.ai) and
[ElevenLabs](https://elevenlabs.io):

- **animation-engine**: idea → finished vertical reel. Voices (tuned for Mongolian), still frames, video shots and
  lip sync on kie.ai, then a frame-exact edit with hand-drawn comic graphics and captions.
- **avatar-maker**: photo of a person → a 3D cartoon avatar set (transparent PNGs, profile picture, talking GIF).
  Good for making the characters you animate.

## Install

In Claude Code:

```
/plugin marketplace add SaagiiSG/goat-academy-plugins
/plugin install animation-engine@goat-academy
/plugin install avatar-maker@goat-academy
```

One-time setup:

1. **kie.ai key**: create one at https://kie.ai/api-key and add credits (1 credit = $0.005).
2. **ElevenLabs key** (for voices): https://elevenlabs.io/app/settings/api-keys
3. Put both in your shell before starting Claude Code:
   - macOS / Linux: add to `~/.zshrc` or `~/.bashrc`:
     `export KIE_API_KEY=...` and `export ELEVENLABS_API_KEY=...`
   - Windows PowerShell: `setx KIE_API_KEY ...` and `setx ELEVENLABS_API_KEY ...`, then open a new terminal
4. Install **ffmpeg** (`brew install ffmpeg`, `winget install ffmpeg`, or `sudo apt install ffmpeg`) and **Pillow**
   (`python3 -m pip install pillow`).

## animation-engine

Ask Claude, for example:

> Make a 20-second reel: a tired café owner does everything alone, and a wise old warrior tells him to build a team
> of AI workers. Mongolian voices, 3D animated style, comic graphics, end with "comment GOAT".

Claude works through the steps with you and shows you each one before spending more:

1. **Story and lines**: hook, one idea, payoff, call to action.
2. **Voices first**: ElevenLabs v4. Line length sets shot length. 2–3 takes per line to pick from.
3. **Look and characters**: three looks (feature-film 3D, comic-book 3D, paper-cut) with tested style sentences.
4. **Still frames** (~4 credits each): everything gets fixed while it's still a picture.
5. **Free animatic**: stills plus voices, so you judge the voices and timing before any video.
6. **Shots**: Grok Imagine for movement, Kling Avatar or OmniHuman for talking faces.
7. **Edit**: fast cuts on the words, "on 2s" comic motion, captions in the lower third, comic words, stickers,
   spinning-head icons, speed lines, phone notifications, rolling counters and an end card.

A 20–30 s reel with a few talking lines costs about **150–300 kie credits ($0.75–1.50)** plus ElevenLabs characters.

It has three skills: **animate** (the whole pipeline), **reel-edit** (the editor, usable on any footage) and
**mn-voice** (voices; Mongolian fixes for з and р). The scripts work without Claude too:

```bash
python3 plugins/animation-engine/scripts/kie.py --help     # any kie.ai model, with resume and no double charges
python3 plugins/animation-engine/scripts/voice.py --help   # ElevenLabs lines, lengths, pauses
python3 plugins/animation-engine/scripts/reel.py --help    # timeline.json -> finished reel
```

**PYNK skill packs:** PYNK Society's free Claude skill packs (3D animation, cartoon episodes, paper-cut, claymation,
documentary, UGC, ad formats) write prompts for specific formats. They aren't included here, but if you've downloaded
them from [their free library](https://app.notion.com/p/Claude-Creative-Skill-Library-Vol-2-3ffb5f1fde2d81938bb9eb76ea6c60d1),
point Claude at the folder: the animate skill uses a pack for the story and prompts, then generates, voices and edits
with this engine.

## avatar-maker

> Make me a cartoon avatar from this photo: ~/Downloads/me.jpg

Claude makes the base portrait and asks you to check the likeness. Then it makes blink and talking frames, cuts out
the background, and gives you `name-base/blink/mid/open.png` (560×560, transparent), `name-profile-1024.png` and
`name-talking.gif`. About 17 credits ($0.09) per avatar.

## Use it fairly

Make characters of yourself, of people who agreed to it, or of public figures only for clearly labelled commentary
or education. Show "AI simulation" on screen when a real person appears, use stock voices (never clone a voice
without consent), and never fake an endorsement.

---

## Монголоор товчхон

Claude Code-д зориулсан 2 плагин:
- **animation-engine**: санаанаас бэлэн Reels хүртэл. ElevenLabs-ийн монгол дуу хоолой, kie.ai дээр зураг, видео,
  уруулын хөдөлгөөн (lip sync), дараа нь комикс график, доод хэсэгт субтитртэй эдит.
- **avatar-maker**: хүний зургаас 3D хүүхэлдэйн аватар.

**Суулгах:** Claude Code дотор

```
/plugin marketplace add SaagiiSG/goat-academy-plugins
/plugin install animation-engine@goat-academy
/plugin install avatar-maker@goat-academy
```

**Тохиргоо:** kie.ai болон ElevenLabs-ийн API key-гээ `KIE_API_KEY`, `ELEVENLABS_API_KEY` нэрээр терминалдаа
тохируулаад, ffmpeg болон Pillow (`python3 -m pip install pillow`) суулгана.

**Ашиглах:** Claude-д "Ядарсан кафены эзэнд Чингис хаан AI баг бүрдүүл гэж зөвлөдөг 20 секундын reel хий" гэх мэтээр
бичнэ. Claude алхам бүрийг танд харуулж, зөвшөөрөл авсны дараа л дараагийн кредитээ зарцуулна. Монгол "з", "р"
авиаг засах арга (дз, рр) mn-voice skill дотор бий.

## License

Code: MIT. Fonts in `plugins/animation-engine/fonts/`: Fira Sans, SIL Open Font License (`OFL.txt`).
