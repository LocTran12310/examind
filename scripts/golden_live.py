"""Golden set against the live stack: rule vs rule_ai, scored with samples/exams/*.expected.json.

EXAMIN_DIR=<folder> runs the 18 official THPT 2025 files instead (rule mode), scored with
apps/api/tests/golden/official_expected.json — official-exam-ingestion AC-08.
"""
import hashlib, json, os, sys, time, shutil, httpx
EX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "samples", "exams")
B = "http://localhost:8088/api"; M = "3e8f301a-5dc4-4db0-9e0d-e29a7ec29278"; OUT = os.environ.get("GOLDEN_OUT", "/tmp/examind-golden")
FILES = ["de-mau-toan10.docx", "de-mau-toan10.pdf", "de-thpt2025-toan.docx", "de-2cot.pdf", "de-kho.docx", "de-scan.pdf", "de-scan.png"]
MODES = {"rule": {"split_mode": "rule", "split_models": []},
         "rule_ai": {"split_mode": "rule_ai", "split_models": [M], "tag_model": M}}
if len(sys.argv) > 1:  # e.g. golden_live.py rule_ai de-mau-toan10.docx
    MODES = {k: v for k, v in MODES.items() if k in sys.argv[1].split(",")}
    FILES = sys.argv[2:] or FILES
c = httpx.Client(timeout=60)
c.post(f"{B}/auth/login", json={"org_code": "trungtama", "username": "admin", "password": "admin123456"}).raise_for_status()
os.makedirs(OUT, exist_ok=True)
stamp = str(time.time())
results = []


def wait(did):
    while (d := c.get(f"{B}/documents/{did}").json())["status"] in ("queued", "parsing", "processing"):
        time.sleep(2)
    return d


if os.environ.get("EXAMIN_DIR"):
    root = os.environ["EXAMIN_DIR"]
    by_hash = {}
    for dirpath, _, names in os.walk(root):
        for n in names:
            if n.endswith(".docx") and not n.startswith("~$"):
                path = os.path.join(dirpath, n)
                by_hash[hashlib.sha256(open(path, "rb").read()).hexdigest()] = path
    golden = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps", "api", "tests", "golden", "official_expected.json")
    tot = {"docs": 0, "questions": 0, "found": 0, "answers": 0, "solutions": 0, "equations": 0, "pictures": 0, "secs": 0.0}
    for doc in json.load(open(golden, encoding="utf-8"))["documents"]:
        src = by_hash[doc["sha256"]]
        # the real file: an existing copy is re-parsed in place (on_duplicate=replace), never duplicated
        r = c.post(f"{B}/documents", files={"file": (os.path.basename(src), open(src, "rb"))},
                   data={"config": json.dumps(MODES["rule"]), "on_duplicate": "replace"}).json()
        d = wait(r["document"]["id"])
        got = {(q["part"], q["number"]): q for q in c.get(f"{B}/documents/{d['id']}/questions").json()}
        steps = {l.get("step"): l for l in d["log"]}
        want = doc["questions"]
        row = {"file": doc["file"][:48], "status": d["status"], "found": sum((w["part"], w["number"]) in got for w in want), "total": len(want),
               "answers": sum(1 for w in want if (q := got.get((w["part"], w["number"]))) and q["answer"] == w["answer"]),
               "solutions": sum(1 for w in want if w["has_solution"] and (q := got.get((w["part"], w["number"]))) and q["solution"]),
               "equations": steps.get("extract", {}).get("equations"), "pictures": steps.get("extract", {}).get("vector_images", 0),
               "secs": round(sum(l.get("ms", 0) for l in d["log"]) / 1000, 1)}
        print(json.dumps(row, ensure_ascii=False), flush=True)
        results.append(row)
        tot["docs"] += 1; tot["questions"] += row["total"]; tot["found"] += row["found"]; tot["answers"] += row["answers"]
        tot["solutions"] += row["solutions"]; tot["equations"] += row["equations"] or 0; tot["pictures"] += row["pictures"]; tot["secs"] += row["secs"]
    print("TOTAL", json.dumps(tot), flush=True)
    json.dump(results, open(f"{OUT}/official.json", "w"), ensure_ascii=False, indent=1)
    sys.exit(0)
for mode, cfg in MODES.items():
    for f in FILES:
        stem, ext = os.path.splitext(f)
        # re-parse the existing copy with this mode instead of uploading a modified duplicate
        r = c.post(f"{B}/documents", files={"file": (f, open(f"{EX}/{f}", "rb"))}, data={"config": json.dumps(cfg), "on_duplicate": "replace"}).json()
        did = r["document"]["id"]
        while (d := c.get(f"{B}/documents/{did}").json())["status"] in ("queued", "parsing", "processing"):
            time.sleep(2)
        qs = c.get(f"{B}/documents/{did}/questions").json()
        exp = json.load(open(f"{EX}/{stem}.expected.json"))
        steps = {l.get("step"): l for l in d["log"]}
        row = {"mode": mode, "file": f, "status": d["status"], "n": len(qs), "error": d["error"],
               "secs": round(sum(l.get("ms", 0) for l in d["log"]) / 1000, 1),
               "ai": steps.get("ai_split"), "triage": steps.get("triage"), "tags": steps.get("suggest_topics")}
        if "questions" in exp:
            truth = exp["questions"]; got = {(q["part"], q["number"]): q for q in qs}
            bad = []
            for t in truth:
                q = got.get((t["part"], t["number"]))
                if not q or q["type"] != t["type"] or q["answer"] != t["answer"] or len(q["options"]) != t["n_options"]:
                    bad.append({"n": t["number"], "part": t["part"], "exp": [t["type"], t["answer"], t["n_options"]],
                                "got": q and [q["type"], q["answer"], len(q["options"]), q.get("parse_method")]})
            row["ok"] = len(truth) - len(bad); row["total"] = len(truth); row["bad"] = bad
            with_topic = [t for t in truth if t.get("topic")]
            if with_topic:
                hit = sum(1 for t in with_topic if (q := got.get((t["part"], t["number"]))) and
                          any(tp["is_primary"] and tp["name"] == t["topic"] for tp in q.get("topics", [])))
                row["topic"] = f"{hit}/{len(with_topic)}"
        else:
            nums = sorted(q["number"] for q in qs if q["number"] is not None)
            key = "png_numbers" if f.endswith(".png") else "numbers"
            row["ok"] = len(set(nums) & set(exp[key])); row["total"] = len(exp[key])
        row["review"] = sum(1 for q in qs if q["status"] == "needs_review")
        results.append(row)
        print(json.dumps({k: row[k] for k in ("mode", "file", "status", "ok", "total", "review", "secs")}, ensure_ascii=False), flush=True)
json.dump(results, open(f"{OUT}/results.json", "w"), ensure_ascii=False, indent=1)
print("DONE", flush=True)
