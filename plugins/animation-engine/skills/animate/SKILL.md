---
name: animate
description: Make a short vertical AI animation (Reels, TikTok, Shorts) from an idea, with 3D or comic-style characters, voices, lip sync, comic graphics and captions, generated on kie.ai and ElevenLabs and cut with ffmpeg. Use when the user wants an animated reel, skit, cartoon ad, explainer or story video, or asks to animate a character or script.
allowed-tools: Bash(python3 *), Bash(python *), Bash(ffmpeg *), Bash(ffprobe *)
---

# Animate: idea → finished reel

Scripts (call them with `python3`; on Windows `python` or `py`):
- `${CLAUDE_PLUGIN_ROOT}/scripts/kie.py`: any kie.ai model (images, video, lip sync). Call it `KIE` below.
- `${CLAUDE_PLUGIN_ROOT}/scripts/voice.py`: ElevenLabs lines, lengths, pauses. See the **mn-voice** skill.
- `${CLAUDE_PLUGIN_ROOT}/scripts/reel.py`: the editor. See the **reel-edit** skill.
- `playbook.md` next to this file: the three looks (feature-film 3D, comic-book 3D, paper-cut), which model for which
  job, prompt formats per video model, the stepped-motion trick. Read it before a bigger piece or a new look.

## Before you start
- `KIE_API_KEY` (https://kie.ai/api-key) and `ELEVENLABS_API_KEY` must be set in the shell Claude Code started from.
  Never ask the user to paste a key into the chat.
- `ffmpeg` and Pillow (`python3 -m pip install pillow`) must be installed.
- `python3 KIE credits`. 1 credit = $0.005. Tell the user what the piece will cost before spending.

## Costs (kie.ai, Nov 2026; check with `KIE price MODEL`)
| Item | Model | Credits |
|---|---|---|
| Still frame / character / keyframe | `nano-banana-2-1` (1K, up to 10 reference images) | 4 |
| Transparent stickers / icon sheet | `gpt-image-2-5-flare-text-to-image` with `background: "transparent"` | 6 |
| Shot without talking | `grok-imagine-video-1-5-preview` (1–15 s) | 2.4/s 480p, 4.5/s 720p, 8/s 1080p |
| Talking shot, any length | `kling/ai-avatar-standard` (image + audio + prompt, works on cartoon faces) | ~10/s |
| Talking shot, 4 s or longer | `omnihuman-2-0` (rejects audio under 4 s) | 14/s |
| Background removal | `recraft/remove-background` | 1 |

Lip sync bills **whole seconds**: keep a line just under a whole number (2.95 s, not 3.05 s). A 20–30 s reel with
4–6 lip-synced lines and 6–10 short shots costs about 150–300 credits ($0.75–1.50).

## The steps
Make one folder per piece: `NN-name/` with `frames/`, `shots/`, `voice/`, and a `README.md` where you log every line,
prompt and credit spent.

**1. Story and lines.** 15–35 s. A hook in the first 2 s, one idea, a clear payoff, then the call to action. Write each
line with the picture it goes over. A talking character gets 1–2 short lines per shot.

**2. Voices first** (mn-voice skill). The length of each line sets the length of its shot. Make 2–3 takes and let the
user pick.

**3. Look and characters.** Pick a look from `playbook.md` and paste its style sentence into every prompt word for
word. Lock each character with one reference image and reuse it in every frame. The **avatar-maker** plugin makes
matching character portraits, and existing art works too. Call each character by the same name in every prompt.

**4. Still frames** (4 credits each). Fix everything while it's still a picture: a still costs 4 credits, 3 s of lip
sync costs 30.
```bash
python3 KIE run nano-banana-2-1 frames/f1-owner.png --input '{"prompt":"Keep this exact character from the reference image, same face, hair and clothes, same 3D animated feature-film style. New scene: ... Vertical 9:16 frame. No text, no logos.","image_input":["@refs/owner.png"],"aspect_ratio":"9:16","resolution":"1K","output_format":"png"}'
```
`@path` uploads a local file. Several at once: write a jobs file and run `KIE batch jobs.json`. Read every frame and
check it: hands and arms (write "exactly two arms and two hands"), faces, stray text. Redo with `--again`. For a new
character, say "exactly the same level of cartoon stylization as the reference … not realistic", or it drifts to a
photo look. A character who doesn't talk in a shot can face away or cover their mouth, so they need no lip sync.

**5. Animatic (free).** Before any video, cut the stills with the voices in reel.py (each cut's `src` can be a PNG)
and show the user. Fix voices, order and timing here.

**6. Shots.**
- No talking, 2–3 s each for fast cuts:
  ```bash
  python3 KIE run grok-imagine-video-1-5-preview shots/s1.mp4 --input '{"prompt":"<style sentence> <the motion, not the picture>. Camera holds completely static, locked off.","image_urls":["@frames/f1-owner.png"],"first_frame_url":"@frames/f1-owner.png","aspect_ratio":"9:16","resolution":"720p","duration":3,"enable_audio":false}'
  ```
  Grok adds a slow push-in by default. When text or an end card goes on top, write "Camera holds completely static,
  locked off, the framing never changes".
- Talking: `python3 KIE run kling/ai-avatar-standard shots/l1.mp4 --input '{"image_url":"@frames/f2.png","audio_url":"@voice/l1.mp3","prompt":"He speaks calmly and warmly to the camera, gentle nods, small hand gestures. Steady camera."}'`
  (or `omnihuman-2-0` with `image_urls`, `audio_url`, `prompt` under 300 characters, `enable_watermark: false`, for
  lines of 4 s or more). If the voice changes later, redo the lip sync, or the mouth won't match.
- Video and lip sync take 1–5 minutes. Use `--timeout 1500`. If a wait times out, run the same command again: the
  task id is saved, so it resumes instead of paying twice.
- Unknown model or an input error (422): `python3 KIE schema MODEL`.

**7. Edit** (reel-edit skill): timeline.json → `reel.py render timeline.json out.mp4 --stills`.

**8. Check.** Read every `-check` frame. Captions must not cover a talking mouth. Graphics must stay in the safe area
(phone app buttons cover the edges and bottom). Spellings must match what's said. Then the user watches it before
anyone posts it.

## Rules learned the hard way
- Fast cuts (0.8–1.5 s on the words) and 2D comic graphics over 3D shots feel alive; long static shots feel like AI.
- Glowing screens, holograms and floating UI read as "AI slop". Use real places and real objects.
- Never name a studio or franchise in a prompt (Pixar, Disney, Spider-Verse): models block or blur it. Describe
  the look instead (`playbook.md`).
- Readable text (labels, counters, notifications, titles) is drawn in the edit, never by the image or video model.
- Real people as characters: show "AI simulation, not the real people" on screen, use stock voices (never clones),
  no logos, and no fake endorsements. Write historical names in full and respectfully (e.g. "Чингис хаан", never
  just "Чингис").

## PYNK skill packs (optional)
PYNK Society publishes free Claude skill packs that write prompts for specific formats: `/3d-animation`,
`/cartoon-episodes`, `/documentary`, `/commercial-pipeline`, `/motion-design` (paper-cut), `/claymation`,
`/paper-animation`, `/talking-object`, `/vox-animation`, `/ugc`, `/ad-director` and more (free library:
https://app.notion.com/p/Claude-Creative-Skill-Library-Vol-2-3ffb5f1fde2d81938bb9eb76ea6c60d1). This plugin doesn't
include them. If the user has them downloaded, ask for the folder, or look for `.claude/skills/*/SKILL.md` or
`skills/*/SKILL.md` inside it. Read the matching pack's SKILL.md and follow it for the story, shot list and prompts.
Then do the making here: `KIE` instead of pasting prompts into a website, the mn-voice skill instead of their edge-tts
voices (for Mongolian), and reel.py for the cut. Their 30 s Seedance blocks cost ~840 credits at 480p, so price them
with `KIE price` first.
