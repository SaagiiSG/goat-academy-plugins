---
name: make-avatar
description: Turn a photo of a person into a 3D cartoon avatar set (transparent PNGs, a profile picture and a talking GIF) with kie.ai. Use when the user asks for a cartoon avatar, bot avatar, profile avatar or talking avatar of themselves or someone else.
allowed-tools: Bash(python3 *), Bash(python *), Bash(py *)
---

# Make a cartoon avatar

One person in, one matching set out (560×560 PNGs with a transparent background, plus a profile picture and a GIF):

| File | What it is |
|---|---|
| `NAME-base.png` | Smiling, mouth closed |
| `NAME-blink.png` | Eyes closed |
| `NAME-mid.png`, `NAME-open.png` | Mouth half and fully open, for talking |
| `NAME-profile-1024.png` | The base on white, 1024×1024 |
| `NAME-talking.gif` | Talk, pause, blink loop on white |

Cost on kie.ai: about **17 credits (~$0.09)** per avatar (base 4, three frames 12, cut-out 1), plus 4 credits once
per computer for the default style reference.

The script is `${CLAUDE_SKILL_DIR}/scripts/avatar.py`. Call it as `SCRIPT` below. On Windows, use `python` or `py`
if `python3` is missing.

## Before you start

1. `python3 -c "import PIL"` must work. If it fails, run `python3 -m pip install pillow`.
2. `KIE_API_KEY` must be set. If it isn't, tell the user to create a key at https://kie.ai/api-key, top up credits,
   and run `export KIE_API_KEY=...` (Windows PowerShell: `$env:KIE_API_KEY="..."`) in the shell Claude Code
   was started from, then restart Claude Code. Never ask them to paste the key into the chat.
3. `python3 SCRIPT credits` shows the balance. Under 17, say so before spending anything.

## Steps

**1. Get photos.** 1–3 clear photos where the face is visible and roughly facing the camera. The user can give file
paths or image URLs. For a public figure, their YouTube channel picture works: fetch the channel page and read the
`og:image` meta tag. Instagram pages need a login, so ask the user for a screenshot or a saved photo instead.

**2. Look at the photos** (Read them) and write `--look`: hair (length, colour, parting), skin tone, facial hair,
glasses, and clothes. Leave out microphones, hands, logos and busy backgrounds.

**3. Base:**
```bash
python3 SCRIPT base avatars/jane-doe --photo photo1.jpg --photo photo2.jpg \
  --look "shoulder-length black hair parted in the middle, light olive skin, clean-shaven, navy knit polo"
```
The folder name becomes the file prefix, so use a short lowercase slug. Read `avatars/jane-doe/work/base.png`. Check
the likeness, the cartoon style, a straight-on centred head and shoulders, and a white background. Show the user
where it is and ask if the likeness is right **before** the next step (12 credits). To retry, run the same command
with a changed `--look` and `--again`. The old one is kept.

Optional `--style ref.png` (repeatable) uses the user's own avatar set as the style reference instead of the default,
so new avatars match an existing set.

**4. Talking frames:** `python3 SCRIPT frames avatars/jane-doe` (blink, mouth half open, mouth open; the three run
at the same time).

**5. Finish:** `python3 SCRIPT finish avatars/jane-doe`. This makes the cut-out (1 credit) and builds every file.
Read `avatars/jane-doe/preview.jpg`. The top row shows the base on dark, colour and white backgrounds. If there's a
thin white or grey outline around the hair on the dark one, run finish again with `--rim gentle` (blonde or light
hair) or `--rim strong` (dark hair). Re-running finish is free. The bottom row shows the four frames. Only the eyes or
mouth should change between them.

## If something goes wrong

- Every kie task id is saved in `work/tasks.json`. Running a step again **resumes** the same task, so a timeout or
  a closed terminal never charges twice. Don't delete `work/` mid-way.
- `402` = not enough credits. `401` = wrong key.
- A failed task is forgotten automatically, so running the step again starts a fresh one.

## Use it fairly

Make avatars of the user, of people who agreed to it, or of public figures for clearly labelled commentary or
education. Never use one to pretend to be the real person, to fake an endorsement, or to put words in their mouth
without saying it's an AI simulation.
