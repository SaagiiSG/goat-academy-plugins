#!/usr/bin/env python3
"""Voices for the animation: ElevenLabs v4 lines, lengths and pauses.

  voice.py say "TEXT" VOICE_ID OUT.mp3 [--lang mn]   one line; prints its length in seconds
  voice.py length FILE                               length in seconds
  voice.py pauses FILE                               where the pauses are (to time captions and cuts)
  voice.py fit IN OUT SECONDS                        trim the end so the clip is at most SECONDS long

Needs ELEVENLABS_API_KEY and ffmpeg. Eleven v4 only works through the text-to-dialogue endpoint, which is
what "say" uses. Your plan allows a few requests at once (3 on the smaller plans), so don't fire more.
"""
import argparse, json, os, re, ssl, subprocess, sys, urllib.error, urllib.request
from pathlib import Path

try:
    import certifi
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = ssl.create_default_context()


def length(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(f)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def say(text, voice, out, lang, model):
    key = os.environ.get("ELEVENLABS_API_KEY") or sys.exit("Set ELEVENLABS_API_KEY first.")
    body = {"inputs": [{"text": text, "voice_id": voice}], "model_id": model}
    if lang:
        body["language_code"] = lang
    req = urllib.request.Request("https://api.elevenlabs.io/v1/text-to-dialogue?output_format=mp3_44100_128",
                                 json.dumps(body).encode(), {"xi-api-key": key, "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, context=CTX, timeout=180) as r:
            Path(out).parent.mkdir(parents=True, exist_ok=True)
            Path(out).write_bytes(r.read())
    except urllib.error.HTTPError as e:
        sys.exit(f"ElevenLabs {e.code}: {e.read().decode()[:400]}")
    print(f"{out}: {length(out):.2f} s")


def pauses(f, noise="-32dB", min_len=0.18):
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(f), "-af", f"silencedetect=n={noise}:d={min_len}",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", err)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", err)]
    print(f"length {length(f):.2f} s")
    for s, e in zip(starts, ends + [length(f)] * (len(starts) - len(ends))):
        print(f"pause {s:.2f} -> {e:.2f}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("say")
    s.add_argument("text")
    s.add_argument("voice")
    s.add_argument("out")
    s.add_argument("--lang", help="language code, e.g. mn for Mongolian")
    s.add_argument("--model", default="eleven_v4")
    sub.add_parser("length").add_argument("file")
    sub.add_parser("pauses").add_argument("file")
    f = sub.add_parser("fit")
    f.add_argument("inp")
    f.add_argument("out")
    f.add_argument("seconds", type=float)
    a = p.parse_args()
    if a.cmd == "say":
        say(a.text, a.voice, a.out, a.lang, a.model)
    elif a.cmd == "length":
        print(f"{length(a.file):.2f}")
    elif a.cmd == "pauses":
        pauses(a.file)
    else:
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", a.inp, "-af",
                        f"atrim=0:{a.seconds},afade=t=out:st={max(0, a.seconds - 0.08)}:d=0.08", a.out], check=True)
        print(f"{a.out}: {length(a.out):.2f} s")


if __name__ == "__main__":
    main()
