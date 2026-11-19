# Avatar Maker: a Claude Code plugin

Turn a photo of a person into a 3D cartoon avatar set: transparent PNGs, a profile picture and a talking GIF.
Claude does the work with [kie.ai](https://kie.ai) image models, for about **$0.09 an avatar**.

You get, for `avatars/jane-doe`:

| File | What it is |
|---|---|
| `jane-doe-base.png` | Smiling, mouth closed (560×560, transparent) |
| `jane-doe-blink.png` | Eyes closed |
| `jane-doe-mid.png`, `jane-doe-open.png` | Mouth half and fully open, for talking |
| `jane-doe-profile-1024.png` | Profile picture on white |
| `jane-doe-talking.gif` | Talk, pause, blink loop |
| `preview.jpg` | Contact sheet to check the result |

## Install

In Claude Code:

```
/plugin marketplace add SaagiiSG/goat-avatar-maker
/plugin install avatar-maker@goat-academy
```

Then set up once:

1. Create a kie.ai API key at https://kie.ai/api-key and add credits ($5 makes about 50 avatars).
2. Put the key in your shell before starting Claude Code:
   - macOS / Linux: add `export KIE_API_KEY=your-key` to `~/.zshrc` or `~/.bashrc`
   - Windows PowerShell: `setx KIE_API_KEY your-key`, then open a new terminal
3. Install Pillow: `python3 -m pip install pillow`

## Use

Ask Claude:

> Make me a cartoon avatar from this photo: ~/Downloads/me.jpg

Claude writes a short description of the person from the photo and makes the base portrait. It asks you to OK the
likeness before spending more, then makes the blink and talking frames and builds every file.

To match an avatar set you already have, give Claude one of those avatars as the style reference.

## How it works

1. **Base** (4 credits): `nano-banana-2-1` gets your photos plus a style reference. The first run makes a fictional
   style reference once (4 credits) and saves it in `~/.cache/avatar-maker/`.
2. **Frames** (12 credits): the base is edited three times (eyes closed, mouth half open, mouth open). Only the eye or
   mouth area is pasted back onto the base, so nothing else moves in the GIF.
3. **Finish** (1 credit): `recraft/remove-background` cuts out the base. The same shape is used for all four frames.

Every kie task id is saved in `work/tasks.json`. If something stops halfway, running the step again picks up the same
task and you don't pay twice.

Without Claude: `python3 plugins/avatar-maker/skills/make-avatar/scripts/avatar.py --help`.

## Use it fairly

Make avatars of yourself, of people who agreed to it, or of public figures for clearly labelled commentary or
education. Don't use one to pretend to be the real person or to fake an endorsement.

---

## Монголоор товчхон

Хүний зургаас 3D хүүхэлдэйн аватар хийдэг Claude Code плагин: тунгалаг PNG, профайл зураг, ярьж буй GIF.
Нэг аватар ойролцоогоор $0.09.

**Суулгах:** Claude Code дотор

```
/plugin marketplace add SaagiiSG/goat-avatar-maker
/plugin install avatar-maker@goat-academy
```

**Нэг удаагийн тохиргоо:**
1. https://kie.ai/api-key дээр API key үүсгээд кредит цэнэглэнэ.
2. Claude Code-оо асаахаас өмнө терминалд `export KIE_API_KEY=таны-key` (Windows: `setx KIE_API_KEY таны-key`).
3. `python3 -m pip install pillow`

**Ашиглах:** Claude-д "Энэ зургаас надад хүүхэлдэйн аватар хийгээд өгөөч: ~/Downloads/me.jpg" гэж бичнэ.
Claude эхлээд үндсэн зургийг хийж, төстэй эсэхийг танаас асууна. Дараа нь нүд ирмэх, ярих хувилбаруудыг хийнэ.

Зөвхөн өөрийн, зөвшөөрсөн хүний, эсвэл AI гэдгийг тодорхой бичсэн нөхцөлд олны танил хүний аватар хийгээрэй.

## License

MIT
