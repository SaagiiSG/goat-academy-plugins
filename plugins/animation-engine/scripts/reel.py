#!/usr/bin/env python3
"""Cut a vertical reel from a timeline file: shots, voices, captions and hand-drawn comic graphics.

  reel.py render TIMELINE.json OUT.mp4 [--stills]    build the reel (--stills also saves one frame per cut to check)
  reel.py split SHEET.png 4x2 camera,chat,... OUTDIR  cut a sprite sheet (transparent PNG grid) into one PNG each

All paths in the timeline are relative to the timeline file. The format is in skills/reel-edit/SKILL.md.
Graphics are drawn at 12 fps ("on 2s"), so they move like hand-drawn comics over smooth 3D shots.
Cuts are trimmed to an exact frame count from the timeline, so pictures never drift off the voice.
Needs Pillow and ffmpeg.
"""
import argparse, json, math, random, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONTS = Path(__file__).resolve().parent.parent / "fonts"
YEL, MAG, CYA, INK = (255, 214, 10), (236, 0, 140), (0, 174, 239), (12, 12, 12)
STILL = {".png", ".jpg", ".jpeg", ".webp"}
GFPS = 12


class Painter:
    def __init__(self, tl, root):
        self.W, self.H = tl.get("size", [1080, 1920])
        self.root = root
        f = tl.get("fonts", {})
        self.comic_font = str(root / f["comic"]) if "comic" in f else str(FONTS / "FiraSansExtraCondensed-Black.ttf")
        self.cap_font = ImageFont.truetype(str(root / f["caption"]) if "caption" in f else str(FONTS / "FiraSans-Bold.ttf"),
                                           tl.get("caption_size", 54))
        self.text_font = str(root / f["text"]) if "text" in f else str(FONTS / "FiraSans-Medium.ttf")
        self.cap_y = tl.get("caption_y", round(self.H * 0.672))  # lower third, under the app's UI-safe area
        self.images = {}

    def img(self, name):
        if name not in self.images:
            im = Image.open(self.root / name).convert("RGBA")
            box = im.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
            self.images[name] = im.crop(box) if box else im
        return self.images[name]

    @staticmethod
    def boil(t, seed):  # hand-drawn jitter: a new pose every graphics frame
        r = random.Random(int(t * GFPS) * 7919 + seed)
        return r.uniform(-4, 4), r.uniform(-4, 4), r.uniform(-3, 3)

    @staticmethod
    def pop(t, t0):  # 0 -> 1.18 -> 1.0 over three graphics frames
        k = (t - t0) * GFPS
        return 0 if k < 0 else [0.5, 1.18, 1.0][int(k)] if k < 3 else 1.0

    def paste(self, canvas, sprite, cx, cy, size, t, seed, rot=0.0):
        if size <= 1:
            return
        dx, dy, dr = self.boil(t, seed)
        s = sprite.copy()
        s.thumbnail((int(size), int(size)), Image.LANCZOS)
        s = s.rotate(rot + dr, resample=Image.BICUBIC, expand=True)
        canvas.alpha_composite(s, (int(cx + dx - s.width / 2), int(cy + dy - s.height / 2)))

    def comic(self, canvas, text, cx, cy, size, t, seed):  # yellow, ink outline, misregistered magenta/cyan plates
        if size < 1:
            return
        dx, dy, _ = self.boil(t, seed)
        f = ImageFont.truetype(self.comic_font, int(size))
        d = ImageDraw.Draw(canvas)
        x, y = cx + dx, cy + dy
        d.text((x + size / 22, y + size / 22), text, font=f, fill=MAG + (230,), anchor="mm")
        d.text((x - size / 45, y - size / 60), text, font=f, fill=CYA + (200,), anchor="mm")
        d.text((x, y), text, font=f, fill=YEL + (255,), anchor="mm", stroke_width=max(4, int(size / 16)), stroke_fill=INK)

    def soft(self, canvas, text, y, font, gap=None, max_w=None):  # plain white with a soft shadow, centred, wraps
        layer = Image.new("RGBA", (self.W, self.H))
        d = ImageDraw.Draw(layer)
        max_w = max_w or self.W * 0.78
        lines, line = [], ""
        for w in text.split():
            test = (line + " " + w).strip()
            if line and d.textlength(test, font=font) > max_w:
                lines.append(line)
                line = w
            else:
                line = test
        gap = gap or round(font.size * 1.22)
        for i, ln in enumerate(lines + [line]):
            d.text((self.W / 2, y + i * gap), ln, font=font, fill="white", anchor="mt")
        shadow = Image.new("RGBA", (self.W, self.H))
        shadow.putalpha(layer.getchannel("A").point(lambda a: a * 0.9))
        canvas.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(7)))
        canvas.alpha_composite(layer)

    def lines_from_centre(self, canvas, t, seed, cx, cy, r0, r1, count, width):
        r = random.Random(seed + int(t * GFPS))
        d = ImageDraw.Draw(canvas)
        for _ in range(count):
            a = r.uniform(0, 2 * math.pi)
            s = r.uniform(*r0)
            d.line([(cx + s * math.cos(a), cy + s * 1.6 * math.sin(a)),
                    (cx + r1 * math.cos(a), cy + r1 * 1.6 * math.sin(a))],
                   fill=(255, 255, 255, 225), width=r.randint(*width))

    def card(self, canvas, lines, cy, t, t0, seed):  # a drawn phone notification with a green tick
        s = self.pop(t, t0)
        if s <= 0:
            return
        w, h = int(self.W * 0.7 * s), int(150 * s)
        layer = Image.new("RGBA", (w + 40, h + 40))
        d = ImageDraw.Draw(layer)
        d.rounded_rectangle((20, 20, 20 + w, 20 + h), radius=int(34 * s), fill=(255, 255, 255, 255), outline=INK, width=6)
        r, cx, cyy = int(42 * s), 20 + int(70 * s), 20 + h // 2
        d.ellipse((cx - r, cyy - r, cx + r, cyy + r), fill=(52, 199, 89, 255), outline=INK, width=4)
        d.line([(cx - r * 0.45, cyy), (cx - r * 0.1, cyy + r * 0.38), (cx + r * 0.5, cyy - r * 0.4)],
               fill="white", width=max(3, int(9 * s)))
        small = ImageFont.truetype(self.text_font, max(8, int(30 * s)))
        big = ImageFont.truetype(self.cap_font.path, max(8, int(42 * s)))
        d.text((20 + int(135 * s), 20 + int(26 * s)), lines[0], font=small, fill=(110, 110, 110, 255))
        d.text((20 + int(135 * s), 20 + int(66 * s)), lines[1], font=big, fill=INK)
        dx, dy, dr = self.boil(t, seed)
        layer = layer.rotate(dr * 0.6, resample=Image.BICUBIC, expand=True)
        canvas.alpha_composite(layer, (int(self.W / 2 + dx - layer.width / 2), int(cy + dy - layer.height / 2)))

    def dizzy(self, canvas, g, t, seed):  # motion arcs and icons circling a head: "my head is spinning"
        u, x, y = t - g["start"], g["x"], g["y"]
        rx, ry = g.get("rx", 290), g.get("ry", 120)
        d = ImageDraw.Draw(canvas)
        turn = 360 * (1.2 * u + 0.9 * u * u)
        for k, (ax, ay) in enumerate([(rx * 0.86, ry * 0.8), (rx * 1.03, ry)]):
            a0 = (turn + k * 160) % 360
            for col, wid in ((INK + (255,), 16), ((255, 255, 255, 255), 8)):
                d.arc((x - ax, y - ay, x + ax, y + ay), a0, a0 + 110, fill=col, width=wid)
        spin = 2 * math.pi * (0.8 * u + 0.9 * u * u)
        names = g.get("images", [])
        for k, name in enumerate(names):
            a = spin + k * 2 * math.pi / len(names)
            depth = 0.75 + 0.25 * math.sin(a)  # smaller at the back of the loop
            self.paste(canvas, self.img(name), x + rx * math.cos(a), y + ry * math.sin(a),
                       g.get("size", 200) * depth * self.pop(t, g["start"] + k * 0.08), t, seed + k)

    def frame(self, tl, t):
        c = Image.new("RGBA", (self.W, self.H))
        for i, g in enumerate(tl.get("graphics", [])):
            if not g["start"] <= t < g["end"]:
                continue
            kind, p, seed = g["type"], self.pop(t, g.get("pop", g["start"])), 100 * (i + 1)
            if kind == "comic":
                text = g["text"]
                if "count" in g:  # rolls from the first number to the second over 0.35 s
                    n0, n1 = g["count"]
                    text = text.replace("{n}", str(round(n0 + (n1 - n0) * min(1.0, (t - g["start"]) / 0.35))))
                self.comic(c, text, g["x"], g["y"], g["size"] * p, t, seed)
            elif kind == "sprite":
                self.paste(c, self.img(g["image"]), g["x"], g["y"], g["size"] * p, t, seed, g.get("rot", 0))
            elif kind == "dizzy":
                self.dizzy(c, g, t, seed)
            elif kind == "speedlines":
                self.lines_from_centre(c, t, seed, g.get("x", self.W / 2), g.get("y", self.H * 0.47),
                                       (380, 640), 1500, 54, (4, 14))
            elif kind == "burst":  # impact lines for two graphics frames
                if t - g["start"] < 2 / GFPS:
                    self.lines_from_centre(c, t - g["start"], seed, g.get("x", self.W / 2), g.get("y", self.H * 0.47),
                                           (560, 760), 1400, 46, (5, 16))
            elif kind == "card":
                self.card(c, g["lines"], g["y"], t, g.get("pop", g["start"]), seed)
            elif kind == "text":
                self.soft(c, g["text"], g["y"], ImageFont.truetype(self.text_font, g.get("size", 36)))
            elif kind == "image":  # a full-frame transparent PNG, e.g. an end card
                a = min(1.0, (t - g["start"]) / g["fade"]) if g.get("fade") else 1.0
                im = self.img_full(g["image"])
                c.alpha_composite(im if a >= 1 else Image.blend(Image.new("RGBA", im.size), im, a))
            else:
                sys.exit(f"Unknown graphic type: {kind}")
        for cap in tl.get("captions", []):
            if cap["start"] <= t < cap["end"]:
                self.soft(c, cap["text"], cap.get("y", self.cap_y), self.cap_font, max_w=self.W * 0.78)
        return c

    def img_full(self, name):
        key = "full:" + name
        if key not in self.images:
            self.images[key] = Image.open(self.root / name).convert("RGBA").resize((self.W, self.H), Image.LANCZOS)
        return self.images[key]


def check(tl):
    cuts = tl["cuts"]
    for a, b in zip(cuts, cuts[1:]):
        if abs(a["end"] - b["start"]) > 1e-6:
            print(f"warning: cut ending at {a['end']} and cut starting at {b['start']} leave a gap or overlap")
    W, H = tl.get("size", [1080, 1920])
    for g in tl.get("graphics", []):  # phone apps cover the edges and the bottom with buttons and the caption
        if "x" in g and "y" in g and not (W * 0.11 <= g["x"] <= W * 0.89 and H * 0.14 <= g["y"] <= H * 0.65):
            print(f"warning: {g['type']} at ({g['x']}, {g['y']}) is outside the safe area "
                  f"x {W * 0.11:.0f}-{W * 0.89:.0f}, y {H * 0.14:.0f}-{H * 0.65:.0f}; app buttons may cover it")


def render(tl_path, out, stills):
    tl_path = Path(tl_path).resolve()
    root, tl = tl_path.parent, json.loads(tl_path.read_text())
    out = Path(out).resolve()
    check(tl)
    W, H = tl.get("size", [1080, 1920])
    fps = tl.get("fps", 24)
    end = tl["cuts"][-1]["end"]
    painter = Painter(tl, root)
    with tempfile.TemporaryDirectory() as tmp:
        for i in range(math.ceil(end * GFPS)):
            painter.frame(tl, i / GFPS).save(f"{tmp}/f{i:05d}.png")
        F = (f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{H},setsar=1,"
             f"format=yuv420p")
        args, vf = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"], []
        for i, c in enumerate(tl["cuts"]):
            a, b, src = c["start"], c["end"], root / c["src"]
            if not src.exists():
                sys.exit(f"Missing file: {src}")
            if src.suffix.lower() in STILL:  # a still frame: free animatic, or a held picture
                args += ["-loop", "1", "-t", f"{b - a + 0.4:.3f}", "-i", str(src)]
            else:
                ss = a - c["sync"] if "sync" in c else c.get("in", 0)  # sync: where this clip's 0 s sits on the timeline
                if ss < 0:
                    sys.exit(f"Cut at {a}: it would start before the clip does (in point {ss:.2f} s)")
                args += ["-ss", f"{ss:.3f}", "-t", f"{b - a + 0.4:.3f}", "-i", str(src)]
            step = {1: "", 2: f",fps={fps / 2}", 3: f",fps={fps / 3}"}[c.get("on", 1)]  # on 2s / on 3s
            frames = round(b * fps) - round(a * fps)  # exact count from the timeline, so cuts never drift
            vf.append(f"[{i}:v]{F},fps={fps}{step},fps={fps},tpad=stop_mode=clone:stop_duration={b - a + 1:.2f},"
                      f"trim=end_frame={frames},setpts=N/{fps}/TB[v{i}]")
        n = len(tl["cuts"])
        sounds = []
        for v in tl.get("voices", []):
            args += ["-i", str(root / v["file"])]
            ms = int(v["at"] * 1000)
            sounds.append(f"[{n + len(sounds)}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                          f"volume={v.get('db', 0)}dB,adelay={ms}|{ms}")
        if "music" in tl:
            args += ["-stream_loop", "-1", "-i", str(root / tl["music"]["file"])]
            sounds.append(f"[{n + len(sounds)}:a]aformat=sample_rates=44100:channel_layouts=stereo,"
                          f"volume={tl['music'].get('db', -18)}dB")
        if not sounds:
            args += ["-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo"]
            sounds.append(f"[{n}:a]anull")
        for k, s in enumerate(sounds):
            vf.append(f"{s}[a{k}]")
        args += ["-framerate", str(GFPS), "-i", f"{tmp}/f%05d.png"]
        vf.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[base]")
        vf.append("".join(f"[a{k}]" for k in range(len(sounds))) +
                  f"amix=inputs={len(sounds)}:normalize=0,apad,atrim=0:{end},loudnorm=I=-16:TP=-1.5:LRA=11[a]")
        vf.append(f"[base][{n + len(sounds)}:v]overlay=eof_action=pass,format=yuv420p[v]")
        args += ["-filter_complex", ";".join(vf), "-map", "[v]", "-map", "[a]", "-t", f"{end}", "-r", str(fps),
                 "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
                 "-movflags", "+faststart", str(out)]
        subprocess.run(args, check=True)
    print(f"{out}: {end:.2f} s, {n} cuts")
    if stills:  # one frame from the middle of every cut, with captions and graphics on, to check by eye
        d = out.with_name(out.stem + "-check")
        d.mkdir(exist_ok=True)
        for i, c in enumerate(tl["cuts"]):
            t = (c["start"] + c["end"]) / 2
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.3f}", "-i", str(out),
                            "-frames:v", "1", "-vf", "scale=540:-2", str(d / f"cut{i + 1:02d}-{t:05.2f}s.jpg")], check=True)
        print(f"check frames: {d}")


def split(sheet, grid, names, outdir):
    cols, rows = (int(x) for x in grid.lower().split("x"))
    im = Image.open(sheet).convert("RGBA")
    cw, ch = im.width // cols, im.height // rows
    Path(outdir).mkdir(parents=True, exist_ok=True)
    for i, name in enumerate(names.split(",")):
        cell = im.crop((i % cols * cw, i // cols * ch, i % cols * cw + cw, i // cols * ch + ch))
        box = cell.getchannel("A").point(lambda a: 255 if a > 40 else 0).getbbox()
        (cell.crop(box) if box else cell).save(Path(outdir) / f"{name}.png")
        print(Path(outdir) / f"{name}.png")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("render")
    r.add_argument("timeline")
    r.add_argument("out")
    r.add_argument("--stills", action="store_true")
    s = sub.add_parser("split")
    for x in ("sheet", "grid", "names", "outdir"):
        s.add_argument(x)
    a = p.parse_args()
    if a.cmd == "render":
        render(a.timeline, a.out, a.stills)
    else:
        split(a.sheet, a.grid, a.names, a.outdir)


if __name__ == "__main__":
    main()
