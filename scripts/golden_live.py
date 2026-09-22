import json, os, sys, time, shutil, httpx
EX = "/Users/macbook/Documents/LocTran/Freelance/examind/samples/exams"
B = "http://localhost:8088/api"; M = "3e8f301a-5dc4-4db0-9e0d-e29a7ec29278"; OUT = "/tmp/claude-502/golden"
FILES = ["de-mau-toan10.docx", "de-mau-toan10.pdf", "de-thpt2025-toan.docx", "de-2cot.pdf", "de-kho.docx", "de-scan.pdf", "de-scan.png"]
MODES = {"rule": {"split_mode": "rule", "split_models": []},
         "rule_ai": {"split_mode": "rule_ai", "split_models": [M], "tag_model": M}}
c = httpx.Client(timeout=60)
c.post(f"{B}/auth/login", json={"org_code": "trungtama", "username": "admin", "password": "admin123456"}).raise_for_status()
stamp = str(time.time())
results = []
for mode, cfg in MODES.items():
    for f in FILES:
        stem, ext = os.path.splitext(f)
        tmp = f"{OUT}/{stem}-{mode}{ext}"; shutil.copy(f"{EX}/{f}", tmp)
        open(tmp, "ab").write(f"\n%{stamp}{mode}".encode())  # new hash → bypass the file cache
        r = c.post(f"{B}/documents", files={"file": (f, open(tmp, "rb"))}, data={"config": json.dumps(cfg)}).json()
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
