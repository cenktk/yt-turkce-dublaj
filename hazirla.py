#!/usr/bin/env python3
"""YouTube videosu icin onceden Turkce dublaj uretir (Chrome eklentisi icin).

  python3 hazirla.py <youtube_url> [--ses nisa,oncel] [--ilk SANIYE]
  python3 hazirla.py serve [--port 8790]
  python3 hazirla.py --selftest
"""
import argparse, concurrent.futures as cf, glob, http.server, json, os, re
import shutil, subprocess, sys, tempfile, urllib.request

KOK = os.path.dirname(os.path.abspath(__file__))
DUBLAJ = os.path.join(KOK, "dublaj")
CLAUDE = shutil.which("claude") or "claude"
TTS_URL = "https://voice.patientdesk.ai/v1/audio/speech"
SESLER = {"nisa": "Kadın (Nisa)", "oncel": "Erkek (Oncel)"}
MAX_TEMPO = 1.35


def altyazi_al(url):
    """-> (video_id, [(start, end, word)]) from en-orig (fallback en) json3."""
    tmp = tempfile.mkdtemp()
    # 'en' often 429s while en-orig succeeds, so ignore the exit code and look at files.
    subprocess.run(["yt-dlp", "--skip-download", "--write-subs", "--write-auto-subs",
                    "--sub-langs", "en-orig,en", "--sub-format", "json3",
                    "-o", os.path.join(tmp, "%(id)s.%(ext)s"), url], capture_output=True)
    files = sorted(glob.glob(os.path.join(tmp, "*.en-orig.json3"))) or \
        sorted(glob.glob(os.path.join(tmp, "*.en.json3")))
    if not files:
        sys.exit("altyazi indirilemedi")
    vid = os.path.basename(files[0]).split(".")[0]
    starts = {}  # ms -> word; keyed by start time so rolling/overlapping events don't duplicate
    for ev in json.load(open(files[0])).get("events", []):
        for s in ev.get("segs") or []:
            w = s.get("utf8", "").strip()
            if w:
                starts.setdefault(ev["tStartMs"] + s.get("tOffsetMs", 0), w)
    t = sorted(starts)
    words = []
    for k, ms in enumerate(t):
        st = ms / 1000
        nxt = t[k + 1] / 1000 if k + 1 < len(t) else st + 2
        # ponytail: word end is estimated from length; json3 has no per-word end times
        words.append((st, min(nxt, st + 0.3 + 0.06 * len(starts[ms])), starts[ms]))
    return vid, words


def birlestir(words, gap=0.8, maxlen=12.0):
    """[(start, end, word)] -> [{start, end, en}] split on .?!, gaps > gap, or length cap."""
    segs, cur = [], []
    for k, w in enumerate(words):
        if cur and w[1] - cur[0][0] > maxlen:
            segs.append(cur); cur = []
        cur.append(w)
        nxt = words[k + 1] if k + 1 < len(words) else None
        if nxt is None or re.search(r"[.?!][\"')\]]*$", w[2]) or nxt[0] - w[1] > gap:
            segs.append(cur); cur = []
    return [{"start": round(c[0][0], 2), "end": round(c[-1][1], 2),
             "en": " ".join(x[2] for x in c)} for c in segs]


def cevir(segs, cache_path):
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}
    todo = [(i, s["en"]) for i, s in enumerate(segs)
            if cache.get(str(i), {}).get("en") != s["en"]]
    for b in range(0, len(todo), 40):
        batch = todo[b:b + 40]
        prompt = (
            "Translate these English video narration segments into natural, spoken Turkish for a voice-over dub.\n"
            "Rules: conversational spoken Turkish, concise; each Turkish line must fit roughly the same speaking "
            "time as the English. Keep product/tech names as-is (Claude, Claude Code, skill, MCP, API, prompt, etc.). "
            "Segments may be sentence fragments; translate each one on its own without merging or moving text.\n"
            "Reply with ONLY a JSON array of objects {\"i\": <same i>, \"tr\": \"...\"}, one per input, no prose, no code fence.\n\n"
            + json.dumps([{"i": i, "en": en} for i, en in batch], ensure_ascii=False))
        for deneme in range(2):
            out = subprocess.run([CLAUDE, "-p", prompt], capture_output=True, text=True, timeout=900).stdout
            try:
                arr = json.loads(out[out.index("["):out.rindex("]") + 1])
                got = {int(o["i"]): str(o["tr"]).strip() for o in arr}
                if set(got) != {i for i, _ in batch} or not all(got.values()):
                    raise ValueError("eksik/fazla i")
                break
            except (ValueError, KeyError, TypeError) as e:
                print(f"  ceviri parse hatasi ({e}), deneme {deneme + 1}", file=sys.stderr)
        else:
            sys.exit("ceviri basarisiz")
        for i, en in batch:
            cache[str(i)] = {"en": en, "tr": got[i]}
        json.dump(cache, open(cache_path, "w"), ensure_ascii=False, indent=1)
        print(f"  cevrildi {b + len(batch)}/{len(todo)}")
    return [cache[str(i)]["tr"] for i in range(len(segs))]


def api_key():
    """Ortam degiskeni, yoksa bu klasorden yukari dogru ilk .env dosyasi."""
    if os.environ.get("PATIENTDESK_API_KEY"):
        return os.environ["PATIENTDESK_API_KEY"]
    d = KOK
    while True:
        env = os.path.join(d, ".env")
        if os.path.exists(env):
            for line in open(env):
                k, _, v = line.strip().removeprefix("export ").partition("=")
                if k.strip() == "PATIENTDESK_API_KEY":
                    return v.strip().strip("'\"")
        if os.path.dirname(d) == d:
            sys.exit("PATIENTDESK_API_KEY yok: ortam degiskeni ya da .env dosyasi ekle")
        d = os.path.dirname(d)


def sure(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", path], capture_output=True, text=True).stdout)


def seslendir(key, ses, metin, slot, wav, mp3):
    if os.path.exists(mp3):
        return
    if not os.path.exists(wav):
        body = json.dumps({"model": "alania-v2", "voice": ses, "input": metin}).encode()
        req = urllib.request.Request(TTS_URL, data=body, headers={
            "Authorization": "Bearer " + key, "Content-Type": "application/json"})
        data = urllib.request.urlopen(req, timeout=180).read()
        open(wav + ".part", "wb").write(data)
        os.replace(wav + ".part", wav)
    tempo = min(MAX_TEMPO, max(1.0, sure(wav) / slot))
    af = ["-af", f"atempo={tempo:.3f}"] if tempo > 1.001 else []
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, *af, "-c:a", "libmp3lame",
                    "-q:a", "4", mp3 + ".part.mp3"], check=True)
    os.replace(mp3 + ".part.mp3", mp3)
    os.remove(wav)  # mp3 is the resume marker; raw 48k WAVs are ~20x bigger


def hazirla(url, sesler, ilk):
    vid, words = altyazi_al(url)
    segs = birlestir(words)
    out = os.path.join(DUBLAJ, vid)
    os.makedirs(out, exist_ok=True)
    n = sum(1 for s in segs if ilk is None or s["start"] < ilk)
    print(f"{vid}: {len(segs)} segment, islenecek {n}")
    tr = cevir(segs[:n], os.path.join(out, "ceviri.json"))
    key = api_key()
    jobs = []
    for ses in sesler:
        os.makedirs(os.path.join(out, ses), exist_ok=True)
        os.makedirs(os.path.join(out, "_wav", ses), exist_ok=True)
        for i in range(n):
            slot = segs[i + 1]["start"] - segs[i]["start"] if i + 1 < len(segs) \
                else segs[i]["end"] + 1.5 - segs[i]["start"]
            jobs.append((key, ses, tr[i], max(slot, 0.3),
                         os.path.join(out, "_wav", ses, f"{i:04d}.wav"),
                         os.path.join(out, ses, f"{i:04d}.mp3")))
    with cf.ThreadPoolExecutor(4) as ex:
        for k, f in enumerate(cf.as_completed([ex.submit(seslendir, *j) for j in jobs]), 1):
            f.result()
            if k % 20 == 0 or k == len(jobs):
                print(f"  ses {k}/{len(jobs)}")
    shutil.rmtree(os.path.join(out, "_wav"), ignore_errors=True)  # only reached when all jobs succeeded
    manifest = {"videoId": vid, "voices": {s: SESLER.get(s, s) for s in sesler}, "segments": [
        {"i": i, "start": segs[i]["start"], "end": segs[i]["end"], "tr": tr[i], "en": segs[i]["en"],
         "files": {s: f"{s}/{i:04d}.mp3" for s in sesler}} for i in range(n)]}
    json.dump(manifest, open(os.path.join(out, "manifest.json"), "w"), ensure_ascii=False, indent=1)
    print(f"tamam: {os.path.join(out, 'manifest.json')}")


class CORS(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


def selftest():
    w = [(0.0, 0.3, "Hello"), (0.4, 0.7, "world."), (0.8, 1.0, "Next"), (2.5, 2.8, "after"),
         (2.9, 3.1, "gap")] + [(4 + k, 4.5 + k, "x") for k in range(15)]
    s = birlestir(w)
    assert [x["en"] for x in s[:3]] == ["Hello world.", "Next", "after gap"], s
    assert all(x["end"] - x["start"] <= 12 for x in s), s
    assert sum(len(x["en"].split()) for x in s) == len(w)
    print("selftest ok")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--selftest"]:
        selftest()
    elif sys.argv[1:2] == ["serve"]:
        p = argparse.ArgumentParser(); p.add_argument("cmd"); p.add_argument("--port", type=int, default=8790)
        port = p.parse_args().port
        os.makedirs(DUBLAJ, exist_ok=True)
        handler = lambda *a, **k: CORS(*a, directory=DUBLAJ, **k)
        print(f"http://localhost:{port}/<videoId>/manifest.json")
        http.server.ThreadingHTTPServer(("127.0.0.1", port), handler).serve_forever()
    else:
        p = argparse.ArgumentParser(); p.add_argument("url")
        p.add_argument("--ses", default="nisa,oncel"); p.add_argument("--ilk", type=float)
        a = p.parse_args()
        hazirla(a.url, [s.strip() for s in a.ses.split(",") if s.strip()], a.ilk)
