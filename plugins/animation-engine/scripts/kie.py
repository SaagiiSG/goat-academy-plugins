#!/usr/bin/env python3
"""Run any kie.ai model from the command line and save the result.

  kie.py credits                       balance
  kie.py price MODEL                   kie's price text for a model
  kie.py schema MODEL                  the model's input fields
  kie.py upload FILE                   upload a local file, print its URL (kept 24 h)
  kie.py run MODEL OUT --input JSON    make one file (image, video, ...) and download it to OUT
  kie.py batch JOBS.json               several at once: [{"model": ..., "out": ..., "input": {...}}, ...]

In --input, any string starting with "@" is a local file: "@frames/a.png" is uploaded and replaced by its URL.
Every task id is saved in tasks.json next to OUT before waiting, so running the same command again resumes the
task instead of paying twice. If OUT already exists nothing runs. Add --again to make a new take (the old file
is kept as NAME.old-N.ext). Needs KIE_API_KEY.
"""
import argparse, json, mimetypes, os, ssl, sys, time, uuid, urllib.request
from pathlib import Path

API = "https://api.kie.ai/api/v1"
UPLOAD = "https://kieai.redpandaai.co/api/file-stream-upload"

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


def discover(path):  # catalog, price and schema share one request a second; wait and retry when limited
    for _ in range(4):
        r = call(f"{API}/models/{path}")
        if r.get("code") != 429:
            return r.get("data") or {}
        time.sleep(1.2)
    sys.exit("kie is rate-limiting model lookups; try again in a few seconds.")


def upload(src):
    path, b = Path(src), uuid.uuid4().hex
    if not path.exists():
        sys.exit(f"No such file: {path}")
    head = (f'--{b}\r\nContent-Disposition: form-data; name="uploadPath"\r\n\r\nanimation-engine\r\n'
            f'--{b}\r\nContent-Disposition: form-data; name="file"; filename="{path.name}"\r\n'
            f'Content-Type: {mimetypes.guess_type(path.name)[0] or "application/octet-stream"}\r\n\r\n')
    r = call(UPLOAD, head.encode() + path.read_bytes() + f"\r\n--{b}--\r\n".encode(),
             {"Content-Type": f"multipart/form-data; boundary={b}"})
    if r.get("code") != 200:
        sys.exit(f"Upload of {path} failed: {r.get('msg')}")
    return r["data"]["downloadUrl"]


def resolve(v):  # "@file" -> uploaded URL, anywhere in the input
    if isinstance(v, str) and v.startswith("@"):
        return upload(v[1:])
    if isinstance(v, list):
        return [resolve(x) for x in v]
    if isinstance(v, dict):
        return {k: resolve(x) for k, x in v.items()}
    return v


def log_path(out):
    return out.parent / "tasks.json"


def tasks(out):
    f = log_path(out)
    return json.loads(f.read_text()) if f.exists() else {}


def save_tasks(out, t):
    log_path(out).write_text(json.dumps(t, indent=1))


def start(model, out, inp):
    out.parent.mkdir(parents=True, exist_ok=True)
    t = tasks(out)
    if out.exists() or out.name in t:
        return
    r = call(f"{API}/jobs/createTask", json.dumps({"model": model, "input": resolve(inp)}).encode(),
             {"Content-Type": "application/json"})
    if r.get("code") != 200:
        sys.exit(f"{out}: kie refused the task ({r.get('code')}: {r.get('msg')}). 402 = not enough credits, "
                 f"422 = a wrong input field (check: kie.py schema {model}).")
    t[out.name] = r["data"]["taskId"]
    save_tasks(out, t)  # saved before waiting, so a crash or timeout never loses a paid task
    print(f"{out}: started (task {t[out.name]})")


def wait(out, timeout):
    if out.exists():
        print(f"{out}: already there")
        return True
    tid, end = tasks(out)[out.name], time.time() + timeout
    while time.time() < end:
        try:
            r = call(f"{API}/jobs/recordInfo?taskId={tid}")
        except OSError:
            r = {}  # network blip: poll again
        d = r.get("data") or {}  # a brand-new task can answer "recordInfo is null" for a few seconds
        if r.get("code") not in (None, 200) and "null" not in str(r.get("msg")):
            print(f"{out}: {r.get('code')} {r.get('msg')}")
            return False
        if d.get("state") == "success":
            res = d.get("response") or json.loads(d.get("resultJson") or "{}")
            urls = res.get("resultUrls") or res.get("result_urls") or []
            if not urls:
                print(f"{out}: finished but returned no file: {json.dumps(res)[:300]}")
                return False
            with urllib.request.urlopen(urls[0], context=CTX, timeout=300) as f:
                out.write_bytes(f.read())
            print(f"{out}: done ({d.get('creditsConsumed')} credits, {d.get('costTime')} s)")
            return True
        if d.get("state") == "fail":
            t = tasks(out)
            t.pop(out.name, None)
            save_tasks(out, t)  # forget it, so the next run starts a fresh task
            print(f"{out}: FAILED ({d.get('failCode')}: {d.get('failMsg')}). Not charged as a rule; run again to retry.")
            return False
        time.sleep(5)
    print(f"{out}: still running (task {tid}). Run the same command again to keep waiting; it won't pay twice.")
    return False


def retire(out):
    t = tasks(out)
    t.pop(out.name, None)
    save_tasks(out, t)
    if out.exists():
        i = 1
        while out.with_name(f"{out.stem}.old-{i}{out.suffix}").exists():
            i += 1
        out.rename(out.with_name(f"{out.stem}.old-{i}{out.suffix}"))


def run_jobs(jobs, again, timeout):
    for j in jobs:
        j["out"] = Path(j["out"])
        if again:
            retire(j["out"])
        start(j["model"], j["out"], j["input"])
    ok = [wait(j["out"], timeout) for j in jobs]  # they all run at once on kie; this just collects them
    if not all(ok):
        sys.exit(1)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("credits")
    for name in ("price", "schema"):
        sub.add_parser(name).add_argument("model")
    sub.add_parser("upload").add_argument("file")
    r = sub.add_parser("run")
    r.add_argument("model")
    r.add_argument("out")
    r.add_argument("--input", required=True, help="the model's input as JSON")
    b = sub.add_parser("batch")
    b.add_argument("jobs")
    for x in (r, b):
        x.add_argument("--again", action="store_true", help="make a new take; keeps the old file as NAME.old-N")
        x.add_argument("--timeout", type=int, default=1500, help="seconds to wait (video and lip sync are slow)")
    a = p.parse_args()
    if a.cmd == "credits":
        print(call(f"{API}/chat/credit").get("data"), "credits")
    elif a.cmd == "price":
        print(discover(f"{a.model}/price").get("pricingDesc"))
    elif a.cmd == "schema":
        doc = discover(f"{a.model}/schema").get("openapi") or sys.exit("kie has no schema for this model yet.")
        body = next(iter(doc["paths"].values()))["post"]["requestBody"]["content"]["application/json"]["schema"]
        inp = body["properties"]["input"]
        for k, v in inp.get("properties", {}).items():
            req = "required" if k in inp.get("required", []) else "optional"
            extra = v.get("enum") or v.get("default", "")
            print(f"{k} ({v.get('type', '?')}, {req}) {extra}: {(v.get('description') or '').splitlines()[0][:140]}")
    elif a.cmd == "upload":
        print(upload(a.file))
    elif a.cmd == "run":
        run_jobs([{"model": a.model, "out": a.out, "input": json.loads(a.input)}], a.again, a.timeout)
    else:
        run_jobs(json.loads(Path(a.jobs).read_text()), a.again, a.timeout)


if __name__ == "__main__":
    main()
