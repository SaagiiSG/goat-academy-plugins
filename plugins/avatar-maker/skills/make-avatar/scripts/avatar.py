#!/usr/bin/env python3
"""Turn a photo of a person into a 3D cartoon avatar set with kie.ai.

  avatar.py credits
  avatar.py base   OUT --photo PHOTO [--photo PHOTO2] --look "hair, skin, clothes" [--style REF ...] [--again]
  avatar.py frames OUT [--again]
  avatar.py finish OUT [--rim off|gentle|strong]

OUT is a folder; its name becomes the file prefix (avatars/jun-yuh -> jun-yuh-base.png ...).
Look at the images between steps. Every kie task id is saved in OUT/work/tasks.json, so running a
step again resumes the same task instead of paying twice. Needs KIE_API_KEY and Pillow.
"""
import argparse, json, mimetypes, os, ssl, sys, time, uuid, urllib.request
from pathlib import Path
from PIL import Image, ImageChops, ImageDraw, ImageFilter

API = "https://api.kie.ai/api/v1"
UPLOAD = "https://kieai.redpandaai.co/api/file-stream-upload"
IMAGE_MODEL, CUTOUT_MODEL = "nano-banana-2-1", "recraft/remove-background"
STYLE_DIR = Path.home() / ".cache" / "avatar-maker"
SIZE = 560
GIF = [("base", 400), ("mid", 120), ("open", 160), ("mid", 120), ("base", 900), ("blink", 120), ("base", 900)]

STYLE_PROMPT = (
    "A 3D animated feature-film character portrait of a fictional friendly adult who is not any real person: head and "
    "shoulders, centred, facing the camera straight on, stylized cartoon proportions with slightly larger eyes, soft "
    "smooth skin, soft even studio lighting, plain pure white background, nothing else in the frame. Warm medium-brown "
    "skin, short dark curly hair, a warm closed-mouth smile, a plain mustard-yellow crew-neck sweater. No text, no logo.")
BASE_PROMPT = (
    "Make a stylized 3D animated cartoon avatar of the person in the first {n} reference image(s), in exactly the same "
    "style, framing and level of cartoon stylization as the last {m} reference image(s) (3D animated feature-film "
    "character portraits): head and shoulders, centred, facing the camera straight on, slightly larger cartoon eyes, "
    "soft smooth skin, soft studio lighting, plain pure white background, nothing else in the frame. They must look like "
    "they belong in the same set as the style reference, not realistic, not a photo, and must take no features from the "
    "style reference person. Keep their likeness: {look}. Warm friendly smile with the mouth closed, eyes looking at the "
    "camera. No microphone, no hands, no text, no logo.")
KEEP = ("Keep everything else exactly identical to the reference image: same pose, same framing, same hair, same "
        "clothes, same lighting, same plain white background, same camera position. Only change: ")
EDITS = {
    "blink": "their eyes are gently fully closed in a natural blink, the mouth stays in the same closed smile.",
    "mid": "their mouth is slightly open mid-word as if talking, lips parted showing a little of the upper teeth, "
           "eyes open looking at the camera.",
    "open": "their mouth is wide open mid-word as if talking enthusiastically, showing the upper teeth and the tongue, "
            "eyes open looking at the camera.",
}

try:  # python.org builds on macOS ship without root certificates
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()


def call(url, data=None, headers=None):
    key = os.environ.get("KIE_API_KEY") or sys.exit("Set KIE_API_KEY first (create one at https://kie.ai/api-key).")
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {key}", **(headers or {})})
    with urllib.request.urlopen(req, context=CTX, timeout=120) as r:
        return json.load(r)


def upload(src):
    if str(src).startswith(("http://", "https://")):
        return str(src)
    path, b = Path(src), uuid.uuid4().hex
    head = (f'--{b}\r\nContent-Disposition: form-data; name="uploadPath"\r\n\r\navatar-maker\r\n'
            f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            f'Content-Type: {mimetypes.guess_type(path.name)[0] or "application/octet-stream"}\r\n\r\n')
    body = head.encode() + path.read_bytes() + f"\r\n--{b}--\r\n".encode()
    r = call(UPLOAD, body, {"Content-Type": f"multipart/form-data; boundary={b}"})
    if r.get("code") != 200:
        sys.exit(f"Upload of {path} failed: {r.get('msg')}")
    return r["data"]["downloadUrl"]


def tasks(work):
    f = work / "tasks.json"
    return json.loads(f.read_text()) if f.exists() else {}


def start(work, name, model, inp):
    """Create a kie task for work/name unless the file or a task for it already exists."""
    t = tasks(work)
    if (work / name).exists() or name in t:
        return
    r = call(f"{API}/jobs/createTask", json.dumps({"model": model, "input": inp}).encode(),
             {"Content-Type": "application/json"})
    if r.get("code") != 200:
        sys.exit(f"{name}: kie refused the task ({r.get('code')}: {r.get('msg')}). 402 means not enough credits.")
    t[name] = r["data"]["taskId"]
    (work / "tasks.json").write_text(json.dumps(t, indent=1))  # saved before waiting, so a crash never loses a paid task


def wait(work, name, timeout=600):
    dest = work / name
    if dest.exists():
        return dest
    tid, end = tasks(work)[name], time.time() + timeout
    while time.time() < end:
        try:
            r = call(f"{API}/jobs/recordInfo?taskId={tid}")
        except OSError:
            r = {}  # network blip: poll again
        d = r.get("data") or {}  # a brand-new task can answer "recordInfo is null" for a few seconds
        if r.get("code") not in (None, 200) and "null" not in str(r.get("msg")):
            sys.exit(f"{name}: {r.get('code')} {r.get('msg')}")
        if d.get("state") == "success":
            res = d.get("response") or json.loads(d.get("resultJson") or "{}")
            with urllib.request.urlopen(res["resultUrls"][0], context=CTX, timeout=120) as f:
                dest.write_bytes(f.read())
            print(f"{name}: done ({d.get('creditsConsumed')} credits)")
            return dest
        if d.get("state") == "fail":
            t = tasks(work)
            t.pop(name)
            (work / "tasks.json").write_text(json.dumps(t, indent=1))  # so the next run starts a fresh task
            sys.exit(f"{name} failed: {d.get('failMsg')}. Run the step again to retry.")
        time.sleep(4)
    sys.exit(f"{name} is still running (task {tid}). Run the same command again to keep waiting; it won't pay twice.")


def retire(work, names):  # --again: keep old results as name.old-N and forget their tasks
    t = tasks(work)
    for n in names:
        t.pop(n, None)
        if (work / n).exists():
            i = 1
            while (work / f"{n}.old-{i}").exists():
                i += 1
            (work / n).rename(work / f"{n}.old-{i}")
    (work / "tasks.json").write_text(json.dumps(t, indent=1))


def style_refs(paths):
    if paths:
        return [upload(p) for p in paths]
    STYLE_DIR.mkdir(parents=True, exist_ok=True)
    if not (STYLE_DIR / "style.png").exists():
        print("First run on this computer: making a fictional style reference (4 credits, once).")
    start(STYLE_DIR, "style.png", IMAGE_MODEL, {"prompt": STYLE_PROMPT, "aspect_ratio": "1:1", "resolution": "1K",
                                                "output_format": "png"})
    return [upload(wait(STYLE_DIR, "style.png"))]


def cmd_base(a):
    work = a.out / "work"
    work.mkdir(parents=True, exist_ok=True)
    if a.again:
        retire(work, ["base.png"])
    if not (work / "base.png").exists() and "base.png" not in tasks(work):
        style = style_refs(a.style)
        photos = [upload(p) for p in a.photo]
        prompt = BASE_PROMPT.format(n=len(photos), m=len(style), look=a.look)
        start(work, "base.png", IMAGE_MODEL, {"prompt": prompt, "image_input": photos + style, "aspect_ratio": "1:1",
                                              "resolution": "1K", "output_format": "png"})
    print(wait(work, "base.png"))


def cmd_frames(a):
    work = a.out / "work"
    if not (work / "base.png").exists():
        sys.exit("Run the base step first.")
    names = [f"{n}-raw.png" for n in EDITS]
    if a.again:
        retire(work, names)
    if any(not (work / n).exists() and n not in tasks(work) for n in names):
        ref = upload(work / "base.png")
        for n, edit in EDITS.items():
            start(work, f"{n}-raw.png", IMAGE_MODEL, {"prompt": KEEP + edit, "image_input": [ref],
                                                      "aspect_ratio": "1:1", "resolution": "1K", "output_format": "png"})
    for n in names:  # the three run at the same time on kie
        wait(work, n)


def changed_box(base, raw, below=0):
    """Box around the band the edit changed most (eyes for blink, mouth for mid/open), padded."""
    d = ImageChops.difference(base, raw).convert("L").point(lambda v: 255 if v > 40 else 0)
    W, H = d.size
    if below:
        ImageDraw.Draw(d).rectangle((0, 0, W, below), fill=0)

    def span(profile):  # run around the peak where change stays above 15% of the peak
        v = list(profile.filter(ImageFilter.BoxBlur(W // 20)).getdata())
        p = max(range(len(v)), key=v.__getitem__)
        if v[p] == 0:
            return None
        lo, hi = p, p
        while lo > 0 and v[lo - 1] > v[p] * 0.15:
            lo -= 1
        while hi < len(v) - 1 and v[hi + 1] > v[p] * 0.15:
            hi += 1
        return lo, hi + 1

    rows = span(d.resize((1, H), Image.BOX).transpose(Image.Transpose.TRANSPOSE))
    if not rows:
        return None
    lo, hi = span(d.crop((0, rows[0], W, rows[1])).resize((W, 1), Image.BOX))
    lo, hi = min(lo, W - hi), max(hi, W - lo)  # the face is centred: mirror the span so both eyes are always in
    pad = W // 40
    return max(0, lo - pad), max(0, rows[0] - pad), min(W, hi + pad), min(H, rows[1] + pad)


def patch(base, raw, box):
    """The base with only the box area taken from raw, soft-edged, so nothing else moves in the GIF."""
    if not box:
        return base.copy()
    m = Image.new("L", base.size, 0)
    ImageDraw.Draw(m).rectangle(box, fill=255)
    out = base.copy()
    out.paste(raw, (0, 0), m.filter(ImageFilter.GaussianBlur(base.width // 64)))
    return out


def peel_rim(img, strength):
    """Drop the thin white/grey rim image models draw around hair: bright, colourless pixels on the outer edge."""
    rounds, bright, grey = {"gentle": (1, 215, 18), "strong": (2, 120, 35)}[strength]
    for _ in range(rounds):
        r, g, b, alpha = img.split()
        mx, mn = ImageChops.lighter(r, ImageChops.lighter(g, b)), ImageChops.darker(r, ImageChops.darker(g, b))
        edge = ImageChops.multiply(alpha.point(lambda v: 255 if v else 0),
                                   alpha.filter(ImageFilter.MinFilter(5)).point(lambda v: 0 if v == 255 else 255))
        kill = ImageChops.multiply(edge, ImageChops.multiply(mx.point(lambda v: 255 if v > bright else 0),
                                                             ImageChops.subtract(mx, mn).point(lambda v: 255 if v < grey else 0)))
        img.putalpha(ImageChops.subtract(alpha, kill))
    return img


def cmd_finish(a):
    work, slug = a.out / "work", a.out.name
    if not all((work / f).exists() for f in ["base.png", "blink-raw.png", "mid-raw.png", "open-raw.png"]):
        sys.exit("Run the base and frames steps first.")
    start(work, "cut.png", CUTOUT_MODEL, {"image": upload(work / "base.png")})
    cut = Image.open(wait(work, "cut.png")).convert("RGBA")
    base = Image.open(work / "base.png").convert("RGB")
    if cut.size != base.size:
        cut = cut.resize(base.size, Image.LANCZOS)
    raw = {n: Image.open(work / f"{n}-raw.png").convert("RGB").resize(base.size) for n in EDITS}
    eyes = changed_box(base, raw["blink"])
    below = eyes[3] if eyes else 0  # the mouth is under the eyes; ignore eye changes in the talking frames
    frames = {"base": base, "blink": patch(base, raw["blink"], eyes),
              "mid": patch(base, raw["mid"], changed_box(base, raw["mid"], below)),
              "open": patch(base, raw["open"], changed_box(base, raw["open"], below))}
    alpha = cut.getchannel("A")  # only the face changes between frames, so one cut-out shape fits all four
    edge = alpha.point(lambda v: 255 if 0 < v < 255 else 0)
    out = {}
    for n, f in frames.items():
        rgba = f.convert("RGBA")
        rgba.putalpha(alpha)
        rgba.paste(cut, (0, 0), edge)  # the cut-out's own soft edge pixels carry no white fringe
        if a.rim != "off":
            rgba = peel_rim(rgba, a.rim)
        out[n] = rgba
        rgba.resize((SIZE, SIZE), Image.LANCZOS).save(a.out / f"{slug}-{n}.png")
    profile = Image.new("RGBA", base.size, "white")
    profile.alpha_composite(out["base"])
    profile.convert("RGB").resize((1024, 1024), Image.LANCZOS).save(a.out / f"{slug}-profile-1024.png")
    gif = []
    for n, _ in GIF:
        f = Image.new("RGBA", (SIZE, SIZE), "white")
        f.alpha_composite(out[n].resize((SIZE, SIZE), Image.LANCZOS))
        gif.append(f.convert("RGB"))
    gif[0].save(a.out / f"{slug}-talking.gif", save_all=True, append_images=gif[1:], duration=[d for _, d in GIF],
                loop=0, optimize=True)
    # preview.jpg: the base on dark, colour and white (to spot edge problems), then the four frames
    s = 360
    sheet = Image.new("RGB", (s * 4, s * 2), "white")
    for i, col in enumerate([(20, 20, 24), (235, 90, 60), (255, 255, 255)]):
        t = Image.new("RGBA", (s, s), col + (255,))
        t.alpha_composite(out["base"].resize((s, s), Image.LANCZOS))
        sheet.paste(t.convert("RGB"), (i * s, 0))
    for i, n in enumerate(["base", "blink", "mid", "open"]):
        sheet.paste(frames[n].resize((s, s), Image.LANCZOS), (i * s, s))
    sheet.save(a.out / "preview.jpg", quality=90)
    print(f"Done: {a.out}/{slug}-{{base,blink,mid,open}}.png, -profile-1024.png, -talking.gif. Check {a.out}/preview.jpg")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("credits")
    b = sub.add_parser("base")
    b.add_argument("out", type=Path)
    b.add_argument("--photo", action="append", required=True, help="photo file or URL of the person (1-3)")
    b.add_argument("--look", required=True, help="hair, skin tone, facial hair, glasses, clothes")
    b.add_argument("--style", action="append", help="your own style reference image(s) instead of the default")
    b.add_argument("--again", action="store_true", help="make a new base (keeps the old one as base.png.old-N)")
    f = sub.add_parser("frames")
    f.add_argument("out", type=Path)
    f.add_argument("--again", action="store_true")
    n = sub.add_parser("finish")
    n.add_argument("out", type=Path)
    n.add_argument("--rim", choices=["off", "gentle", "strong"], default="off",
                   help="remove a white outline around the hair (gentle for blonde or light hair)")
    a = p.parse_args()
    if a.cmd == "credits":
        print(call(f"{API}/chat/credit").get("data"), "credits")
    else:
        {"base": cmd_base, "frames": cmd_frames, "finish": cmd_finish}[a.cmd](a)


if __name__ == "__main__":
    main()
