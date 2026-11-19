# AI animation playbook (kie.ai)

Written 17 Nov 2026 from two web research passes and the live kie.ai model specs. Prices and
model inputs were read from the kie.ai API that day. They change, so re-check before a big run.
Anything marked **[test]** is reported online but not tried yet.

---

## 1. The pipeline — 9 steps

The short version is "pick a style → make characters → write a 0–1 s sequence prompt". Pros add the steps in
between, because a still image costs ~$0.02 and a video clip costs ~$0.70.
**Fix everything you can while it is still a picture.**

| # | Step | What you make | Tool on kie.ai |
|---|---|---|---|
| 1 | Story | Logline → beat sheet → script with dialogue | Claude |
| 2 | Voices | Record or generate the lines **first**. Line length sets shot length. | ElevenLabs `eleven_v4` (`voice.py say`, mn-voice skill) |
| 3 | Style bible | 2–4 approved style frames + **one style sentence** pasted into every prompt, word for word + a banned-word list | image model |
| 4 | Characters | One locked master image → headshot, full body, turnaround (front, ¾, side, back), expression sheet, prop sheets | `nano-banana-2-1` (10 refs, 4 cr), `gpt-image-2-6/economy-image-to-image` (5 cr) |
| 5 | Places | 3–5 empty versions of each location. Pick one. Reuse it everywhere. | same |
| 6 | Storyboard | Rough frames, one per shot | same, or stick figures |
| 7 | Keyframes | Character placed on the location in the start pose (and end pose) | image-edit model |
| 8 | Video | Draft cheap → pick takes → re-render the keepers on the good model | see §3 |
| 9 | Finish | Edit, retime, lip sync, music, SFX, upscale, colour | ffmpeg / Resolve, `topaz/video-upscale` |

**Rules that save the most money**
- Generate 5–10 s per shot, keep 2–6 s. Takes drift after 5–8 s.
- Budget **4–6 takes per kept shot**, more for action.
- One camera move per shot.
- Never use the full reference limit. 1–2 character images + 1 place + 1 motion ref is the sweet spot.
- Big action melts. Split it into short clips.

---

## 2. The three looks

### Never name the studio

Kling and Seedance are reported to block "Pixar" and "Spider-Man". Disney sent cease-and-desist
letters to Google (Dec 2025) and ByteDance (Feb 2026). Even when a name gets through, the model
gives you its blurry average of that studio. **Describe what you see instead.** [test: style-only
names on each model]

### A. Feature-film 3D (the Pixar / Disney look)

**What you see**
- Round, chubby, exaggerated shapes. Big head, big eyes.
- Eyes: glossy, with a bright **catchlight**, clear cornea bulge.
- Skin glows where light passes through (ears, nose, fingers) — *subsurface scattering*.
- Simple hand-painted textures, not pores.
- Warm vs cool light tells the story. Soft key light, rim light that separates the character, bounce light.
- Shallow depth of field, real-lens feel. Shape language per world (soft curves = safe, hard edges = cold).
- One theme colour runs through the whole film.

**How it moves**: smooth (on 1s, 24 fps), with motion blur. The 12 principles: squash and stretch,
anticipation, overshoot, follow-through, arcs, holds.

**Style sentence (paste every time)**
> Soft rounded 3D animated feature style, stylized proportions and simplified forms, large expressive
> eyes with bright catchlights, subsurface scattering on the skin, hand-painted texture detail, warm key
> light with a soft cool rim light, global illumination, shallow depth of field.

**Motion add-on**
> Pose-to-pose acting: stillness → anticipation → sudden acceleration → overshoot → sharp stop, hair and
> sleeves follow through late. Hold key poses 0.1–0.2 s.

**Banned words**: photorealistic, anime, "cartoon" (goes flat 2D), masterpiece, Unreal Engine, the studio name.

**Fixes**
- Looks plastic → add material + light words (subsurface scattering, key light direction, depth of field).
- Face drifts uncanny → make the keyframe in an image model first, then animate it.
- Floaty, even motion → use the motion add-on.

### B. Comic-book 3D (the Spider-Verse look)

**What you see**
- Halftone / Ben-Day dots and hatch lines used **as shading**.
- Hand-drawn ink lines on top of the 3D (faces and hands at least).
- Background blur is replaced by **colour plates slipping apart** (CMYK misregistration, chromatic offset).
- **No motion blur.** Speed lines and smear frames instead.
- Comic sound words on screen (KRACK), panels, captions.
- Each "world" gets its own medium: watercolour, punk Xerox collage, Indian comic print.

**How it moves**: characters on **2s** (each pose held 2 frames = 12 poses a second), camera on 1s.
A character switches to 1s when they gain confidence. Smears last 1–2 frames.

**Style sentence**
> Stylized comic-book 3D animation, halftone dot shading and cross-hatched shadows, bold hand-inked
> outlines over the 3D forms, CMYK misregistration instead of depth of field, speed lines and smear
> frames instead of motion blur, high-contrast saturated palette, stepped animation on 2s.

**Banned words**: fluid motion, motion blur, bokeh, shallow depth of field, Unreal Engine 5,
Spider-Man / Spider-Verse.

**Fixes**
- Comes out smooth → it will. Every video model renders smooth motion. **Retime in post** (§5). Keep
  the camera locked or slow, because retiming steps the camera too.
- Halftone looks digital → build it in the still in passes (warp → ink bleed → halftone), 4K, then animate.
- Comic looks hide AI mistakes. That's a bonus: glitches read as style.

### C. Paper-cut stop-motion

**What you see**
- Matte coloured card. Visible fibres. Torn or deckled edges.
- **Real shadows between layers.** 2–3 layers of depth (more and they merge).
- Raking light that shows the paper grain.
- Pieces are flat cut-outs, hinged at joints like puppets.
- Shot like a real object on a table, not like a drawing.

**How it moves**: pieces slide, drop, step, or rotate in. One step per beat. **8–12 fps**, stepped.
Camera locked or a slow push. Pieces never fold or bend like cloth.

**Style sentence**
> Hyper-real macro photograph of a handmade paper-cut stop-motion set: matte coloured cardstock, visible
> paper fibres, torn and deckled edges, 2–3 dimensional stacked paper layers with soft real shadows
> between them, raking side light, slight handmade imperfection, stop-motion at 12 frames per second.

**Motion add-on**
> Every piece is a flat pre-cut shape that slides, drops or rotates in from outside the frame. No
> folding, no bending, no constructing in place. Camera holds completely static.

**Banned words**: origami, folded, glossy, collage, readable text, smooth parallax.

**Fixes**
- Paper turns to plastic → "matte paper, visible fibre", raking light.
- Character holds paper instead of being paper → "a cut-out figure made of torn card".
- **Idea [test]**: `seedream/5-5-layer-decomposition` splits one image into transparent PNG layers.
  That gives true multiplane depth: move the layers in the editor and skip video models for some shots.

---

## 3. Which kie.ai model for which job

1 credit = $0.005. Prices read 17 Nov 2026.

| Job | Model | Why | Price |
|---|---|---|---|
| **Cheap look tests** | `veo-3-1` with `model: veo3_lite` | 8 s clip, first+last frame | 30 cr per clip (720p) |
| Cheap look tests | `google/gemini-omni-flash-1-2` | has a seed, 6 refs, 360p drafts | 4 cr/s (360p), 9 cr/s (720p) |
| **Animate between key poses** | `kling-4.0/keyframe-to-video` | first + up to 8 middle + last frame, 3–30 s. Real in-betweening. | 28.5 cr/s (720p) |
| Same, cheaper | `kling-4.0/flash-keyframe-to-video` | 3–20 s | 17 cr/s (720p) |
| **Same cast across many shots** | `kling-4.0/reference-to-video` | 7 named characters (2–4 views each), 3 voices | 28.5 cr/s (720p, no video in) |
| **Several cuts in one go** | `kling-3.0/video` with `multi_shots: true` | up to 5 shots, each its own prompt + length | 15.1 cr/s (720p, no sound) |
| Storyboard → film | `bytedance/seedance-2-5` | 30 ref images, "Use Images 1 to 7 in order as keyframes", draft mode | 28 cr/s (480p draft) |
| Lip sync, stylized face | `omnihuman-2-0` | image + audio, handles cartoon faces | 14 cr/s |
| Characters & keyframes | `nano-banana-2-1` | 10 refs, holds identity | 4 cr (1K) |
| Paper layers | `seedream/5-5-layer-decomposition` | image → transparent layers | per layer |

**Hard limits to remember**
- Seedance 2.5, Wan 3.0 and Gemini Omni: **frames OR references, never both** in one call. Pick per shot.
- Veo reference mode: 1–3 images, 8 s only, Fast/Lite only.
- Kling 3.0 multi-shot: 500 characters per shot. Each `@element` uses 37 of them.
- Only Wan 3.0 and Gemini Omni take a seed. Seeds are for A/B tests, not for keeping a character.

---

## 4. Prompt formats that each model actually follows

**Second-by-second prompts ("0–1 s: …") work, but not everywhere.**
- Works: Kling 4.0, Seedance **2.5**, Veo 3.1, Wan 3.0.
- **Seedance 2.0 ignores timestamps.** Use "Shot 1 / Shot 2" with it.

### Kling 4.0 (keyframe or reference)
```
[Asset roles] @first_frame is the opening pose. @keyframe_1 is the jump peak. @last_frame is the landing.
@Hero is the girl in the yellow raincoat — keep her face, hair and coat exactly.
[Style] <style sentence>
[Sequence]
0–1 s: @Hero crouches, anticipation, camera static.
1–3 s: she springs up to @keyframe_1, overshoot, coat trails behind.
3–5 s: she lands as in @last_frame, squash on impact, slow push-in.
[Audio] Rain on tin roof, one splash on landing, no music.
```
Keep the timeline in the same order as the keyframes. Only add a keyframe when the picture really changes.

### Kling 3.0 multi-shot (`multi_prompt`)
```
Shot 1 (3 s): wide, @Hero runs across the rooftop, handheld tracking.
Shot 2 (2 s): close-up of her shoes skidding on wet tin, static.
Shot 3 (3 s): low angle, she leaps the gap, camera tilts up.
```
Dialogue: `Hero (whispering, scared): Don't look down.`

### Seedance 2.5
```
Use Images 1 to 5 in order as keyframes.
<style sentence>
[0s-2s] … [2s-5s] … [5s-8s] …
Throughout the video, characters with identical appearance are prohibited. No twin effect.
Keep it subtitle-free. No BGM.
```
Sound marks: music `()`, sound effects `<>`, dialogue `{text}`.

### Veo 3.1
```
[00:00-00:02] Medium shot, <subject>, <action>. <style sentence>
[00:02-00:04] Reverse shot … SFX: rustling leaves. Ambient noise: distant traffic.
```
Say what you want, not what you don't: "an empty field" instead of "no buildings".

**For every model**
- If you give a start frame, **describe the motion, not the picture**. The model can already see the picture.
- Call each character by the **same name every time**. No "she", no "the girl".
- 60–100 words per shot is plenty. Never paste the whole script.
- Write "camera holds completely static", not "no camera movement".

---

## 5. The stepped-motion trick (Spider-Verse and paper-cut)

No video model has a frame-rate setting. They all render smooth. Fix it after:

```bash
# "on 2s" — Spider-Verse feel (12 poses a second on a 24 fps timeline)
ffmpeg -i in.mp4 -vf "fps=12,fps=24" -c:a copy out_on2s.mp4

# "on 3s" — paper-cut / stop-motion feel (8 poses a second)
ffmpeg -i in.mp4 -vf "fps=8,fps=24" -c:a copy out_on3s.mp4
```

Better still for paper-cut: make the poses as **stills** and hold each one for 2–3 frames in the edit.

---

## 6. Sound

- The video models' built-in audio picks a **new random voice every time**. Bad for a recurring character.
- Do this instead: make dialogue first (ElevenLabs), then pin it with a voice reference
  (Kling 4.0 `voices` or an element's `voice_url`; Seedance "reference the timbre in Audio 1").
- Music (Suno) and sound effects separately, mixed in the edit.
- Cartoon lip sync: `kling/ai-avatar-standard` (any length) or OmniHuman (4 s or more). Both handle stylized human
  faces; non-human faces (objects, animals) are less reliable.
- **Mongolian:** ElevenLabs `eleven_v4` with `language_code: mn` (mn-voice skill).

---

## 7. What a 30-second piece costs (estimate)

6 shots × 5 s. An estimate from the prices above, not a quote.

| Part | Count | Credits |
|---|---|---|
| Character sheets + keyframes | ~25 images × ~5 cr | ~125 |
| Draft takes (Veo Lite) | 6 shots × 4 takes × 30 cr | ~720 |
| Final takes (Kling 4.0 keyframe, 720p) | 6 shots × 2 takes × 142.5 cr | ~1,710 |
| Upscale (Topaz 2×) | 30 s × 8 cr | ~240 |
| **Total** | | **~2,800 cr ≈ $14** |

---

## 8. Still to test before trusting it

- Does a style-only name ("Spider-Verse inspired") get blocked on Kling / Veo / Seedance through kie.ai?
- Does a Seedance 2.5 draft keep the same motion when upgraded to 1080p?
- Does Seedream layer split give clean enough paper layers for multiplane shots?
- Which model holds a stylized face best over 5 shots: Kling 4.0 reference vs Seedance 2.5?

---

## Sources (main ones)

- Kling 4.0 guide — kling.ai/quickstart/kling-4-model-user-guide; keyframes — kling.ai/blog/kling-4-multiple-keyframes-guide
- Kling 3.0 guide — kling.ai/quickstart/klingai-video-3-model-user-guide
- Seedance 2.0 / 2.5 guides — docs.byteplus.com/en/docs/modelark/seedance-2-0-prompt-guide, docs.byteplus.com/en/docs/ModelArk/2607689
- Veo 3.1 guide — cloud.google.com/blog/products/ai-machine-learning/ultimate-prompting-guide-for-veo-3-1
- Wan 3.0 guide — help.aliyun.com/en/model-studio/wan3-video-generation-guide
- Spider-Verse craft — fxguide.com/?p=244678, foundry.com/insights/film-tv/graphic-look-in-comp-spiderman, beforesandafters.com (Across the Spider-Verse inking + Hobie frame rates)
- Pixar craft — vfxvoice.com/discovering-elio, studiodaily.com (Inside Out lenses)
- Paper-cut — animationobsessive.substack.com/p/magic-paper, melies.co/cinematic-techniques/viral-looks/paper
- Studio-name filters — the-decoder.com, axios.com/2026/02/13/disney-bytedance-seedance, dataconomy.com (Gemini Disney block)
- Cost / takes — mindstudio.ai (Seedance short film cost), petapixel.com (Kalshi ad, 300–400 gens for 15 clips)
