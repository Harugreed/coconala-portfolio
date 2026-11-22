"""台本（script/*.json）の各文を Irodori-TTS サーバーで読み上げ、文ごとの WAV と時刻表（timing.json）を作る。

  python tools/synth.py script/telop-main.json public/voice/main --ref <お手本WAV>

サーバー：OMOIKANE/tools/explainer/irodori_server.py（127.0.0.1:10212）。
出力先はサーバーの制約で OMOIKANE の中に一度書き、ここへコピーする。
"""
import json, re, shutil, sys, time, urllib.request, wave
from pathlib import Path

SCRIPT, OUTDIR = Path(sys.argv[1]), Path(sys.argv[2])
REF = sys.argv[sys.argv.index("--ref") + 1]
SERVER = "http://127.0.0.1:10212"
STAGE = Path(r"C:/Users/haruk_26upb8u/ClaudeProject/OMOIKANE/build/coconala-tts")
GAP = 0.45      # 文と文の間（秒）
SCENE_GAP = 0.8 # 場面の切り替えの間（秒）
SEED = 14

def post(path, body):
    req = urllib.request.Request(SERVER + path, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())

def spoken(text):
    return re.sub(r"\[\[|\]\]", "", text)

def main():
    data = json.loads(SCRIPT.read_text(encoding="utf-8"))
    OUTDIR.mkdir(parents=True, exist_ok=True); STAGE.mkdir(parents=True, exist_ok=True)
    for _ in range(120):
        try:
            urllib.request.urlopen(SERVER + "/health", timeout=5); break
        except Exception:
            time.sleep(5)
    t = 0.6
    timing = []
    n = 0
    for sc in data["scenes"]:
        start = t
        items = []
        for line in sc["lines"]:
            n += 1
            name = f"s{n:02d}.wav"
            stage = STAGE / name
            if not (OUTDIR / name).exists():
                res = post("/synth", {"text": spoken(line), "out": str(stage), "ref_wav": REF, "seed": SEED})
                shutil.copy(stage, OUTDIR / name)
            with wave.open(str(OUTDIR / name)) as w:
                dur = w.getnframes() / w.getframerate()
            items.append({"file": name, "text": line, "start": round(t, 3), "dur": round(dur, 3)})
            print(f"{n:02d} {dur:5.2f}s {spoken(line)[:30]}", flush=True)
            t += dur + GAP
        if not sc["lines"]:
            t += 4.0  # 文のない図解の場面は4秒
        t += SCENE_GAP - (GAP if sc["lines"] else 0)
        timing.append({"id": sc["id"], "start": round(start, 3), "end": round(t, 3), "visual": sc["visual"], "chapter": sc["chapter"], "lines": items})
    out = {"title": data["title"], "total": round(t + 0.8, 3), "scenes": timing}
    (OUTDIR / "timing.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("total", out["total"])

main()
