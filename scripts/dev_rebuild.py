"""Rebuild a development stack from an empty database: the org, its admin, and every paper re-ingested.

Meant for the step after `docker compose down -v && make up`, which leaves nothing but the migrations, the system
org and the super admin. From there this drives the real HTTP API — the same endpoints a person would click — so
what it produces is what the product produces, not a fixture that happens to resemble it.

    python3 scripts/dev_rebuild.py --papers /path/to/docx            # the whole walk
    python3 scripts/dev_rebuild.py --papers /path/to/docx --skip-org # org already there, only upload
    python3 scripts/dev_rebuild.py --status                          # what the stack holds right now

**Development only, and it refuses to pretend otherwise.** It expects an empty org and will not delete anything:
if the org already exists it says so and stops unless `--skip-org`. The wipe itself is deliberately *not* here —
`docker compose down -v` is one command, and hiding it inside a script is how a destructive step becomes a habit.

Credentials come from `.env` (the super admin the bootstrap made) and `.ai/credentials.env` (the org and the
password to give its admin, so `make verify` and the e2e walk keep working afterwards). Neither is ever printed.

Why every paper is re-uploaded rather than the levels backfilled: a question's level from the model depends on
which questions share its batch, and the pipeline batches per paper in the paper's own order — so a level set at
parse time is reproducible and its neighbours mean something, while one set by a bulk pass over the whole bank is
an artefact of the order that pass happened to read in (difficulty-at-upload ADR-03).
"""
import argparse
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = os.environ.get("EXAMIND_URL", "http://localhost:8088")
POLL_SECONDS = 5
SYSTEM_ORG = "system"  # where the bootstrap puts the super admin
#: a 40-question paper goes through extraction, topic tagging and the difficulty pass; the model half alone is
#: ~4 batches of 10 at a few seconds each, so a paper is minutes rather than seconds
PAPER_TIMEOUT = 900


def env_file(path: pathlib.Path) -> dict:
    out = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


class Api:
    """Just enough HTTP for this walk: a cookie jar, JSON in, JSON out, and errors that say what came back."""

    def __init__(self, base: str):
        self.base, self.cookies = base, {}

    def _request(self, method: str, path: str, body=None, files=None):
        url = f"{self.base}{path}"
        headers = {}
        if files is not None:
            boundary = "----examind-rebuild"
            name, data = files
            parts = [f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{name}\"\r\n"
                     f"Content-Type: application/octet-stream\r\n\r\n".encode() + data + b"\r\n"]
            for field, value in (body or {}).items():
                parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"\r\n\r\n{value}\r\n".encode())
            payload = b"".join(parts) + f"--{boundary}--\r\n".encode()
            headers["content-type"] = f"multipart/form-data; boundary={boundary}"
        elif body is not None:
            payload = json.dumps(body).encode()
            headers["content-type"] = "application/json"
        else:
            payload = None
        if self.cookies:
            headers["cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                for header in r.headers.get_all("set-cookie") or []:
                    k, _, v = header.split(";")[0].partition("=")
                    self.cookies[k] = v
                raw = r.read()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:400]
            raise SystemExit(f"{method} {path} → {e.code}\n  {detail}") from None

    def get(self, path):
        return self._request("GET", path)

    def post(self, path, body=None, files=None):
        return self._request("POST", path, body, files)


def login(api: Api, org: str, user: str, password: str) -> dict:
    """Every login names an org, the super admin included — it lives in the system org like anyone else."""
    return api.post("/api/auth/login", {"org_code": org, "username": user, "password": password})


def ensure_password(api: Api, user: str, current: str, wanted: str) -> None:
    """Land `user` on `wanted` with `must_change_password` cleared, going through the product to do it.

    The bootstrap's super admin and a freshly created org admin both start with the flag set, and the product
    refuses every request until it is cleared. Clearing it means an actual change — the handler rejects a new
    password equal to the old one — so when the password is already the one we want, it goes out to a throwaway
    and straight back. Two calls, and `.env` stays the one place that says what the password is.
    """
    def change(frm: str, to: str) -> None:
        api.post("/api/auth/change-password", {"current_password": frm, "new_password": to})

    if current == wanted:
        via = f"{wanted}-doi-tam"
        change(wanted, via)
        change(via, wanted)
        print(f"  xoá cờ đổi mật khẩu cho {user} (mật khẩu giữ nguyên như .env)")
    else:
        change(current, wanted)
        print(f"  đặt mật khẩu cho {user} theo .ai/credentials.env")


def register_model(api: Api, name: str, model: str, base_url: str) -> str | None:
    """Register the org's classification model and make it the one ingestion uses.

    A new org has none, and without it the pipeline's model half silently does not run: topics fall back to the
    keyword cues and every level comes from the position rule. Nothing fails, which is exactly what makes it easy
    to miss — the papers just parse suspiciously fast (difficulty-at-upload A-02).
    """
    made = api.post("/api/ai-models", {"name": name, "provider": "ollama", "model": model, "base_url": base_url,
                                       "capabilities": ["text"], "is_free": True, "enabled": True})
    model_id = made["id"]
    api._request("PUT", "/api/org/settings/ingestion", {"tag_model": model_id})
    got = api.get("/api/org/settings/ingestion")
    if got.get("tag_model") != model_id:
        sys.exit(f"đăng ký được model nhưng tổ chức không nhận: {got}")
    print(f"  {model} đã đăng ký và được đặt làm model phân loại của tổ chức")
    return model_id


def status(api: Api) -> None:
    me = api.get("/api/auth/me")
    docs = api.post("/api/documents/search", {"page": 1, "limit": 1})
    qs = api.post("/api/questions/search", {"page": 1, "limit": 1, "status": "all"})
    print(f"  đang là {me['username']} ({me['role']}) · {docs['total']} đề nguồn · {qs['total']} câu hỏi")


def upload_papers(api: Api, papers: list[pathlib.Path]) -> list[str]:
    ids = []
    for i, p in enumerate(papers, 1):
        r = api.post("/api/documents", {"meta": "{}", "config": "{}"}, files=(p.name, p.read_bytes()))
        ids.append(r["document"]["id"])
        print(f"  [{i}/{len(papers)}] {p.name[:70]}")
    return ids


def wait_for(api: Api, ids: list[str]) -> dict:
    """Poll until every document has left `queued`/`processing`. The worker runs one at a time by default."""
    began, seen = time.monotonic(), {}
    budget = PAPER_TIMEOUT * max(1, len(ids))
    while time.monotonic() - began < budget:
        rows = api.post("/api/documents/search", {"page": 1, "limit": 100})["data"]
        seen = {d["id"]: d["status"] for d in rows if d["id"] in ids}
        left = [i for i, s in seen.items() if s in ("queued", "processing")]
        done = len(ids) - len(left)
        print(f"  {done}/{len(ids)} xong · còn {len(left)} đang chạy · {round(time.monotonic() - began)}s", end="\r", flush=True)
        if not left:
            print()
            return seen
        time.sleep(POLL_SECONDS)
    print()
    sys.exit(f"hết thời gian chờ: {sum(1 for s in seen.values() if s in ('queued', 'processing'))} đề còn đang chạy")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--papers", default=None, help="thư mục chứa .docx để upload lại")
    ap.add_argument("--skip-org", action="store_true", help="tổ chức đã có, chỉ upload")
    ap.add_argument("--status", action="store_true", help="chỉ xem stack đang có gì")
    ap.add_argument("--model", default="qwen2.5:7b", help="model ollama để đăng ký làm model phân loại")
    ap.add_argument("--no-model", action="store_true", help="không đăng ký model (chỉ quy tắc vị trí)")
    args = ap.parse_args()

    dotenv = env_file(ROOT / ".env")
    creds = env_file(ROOT / ".ai" / "credentials.env")
    su_user = dotenv.get("SUPERADMIN_USERNAME")
    su_pass = dotenv.get("SUPERADMIN_PASSWORD")
    org_code, org_user, org_pass = creds.get("LOCAL_ORG"), creds.get("LOCAL_USER"), creds.get("LOCAL_PASSWORD")
    missing = [n for n, v in (("SUPERADMIN_USERNAME", su_user), ("SUPERADMIN_PASSWORD", su_pass),
                              ("LOCAL_ORG", org_code), ("LOCAL_USER", org_user), ("LOCAL_PASSWORD", org_pass)) if not v]
    if missing:
        sys.exit(f"thiếu biến: {', '.join(missing)} (.env và .ai/credentials.env)")

    api = Api(BASE)
    if args.status:
        login(api, org_code, org_user, org_pass)
        return status(api)

    if not args.skip_org:
        print(f"1. đăng nhập super admin trên {BASE}")
        login(api, SYSTEM_ORG, su_user, su_pass)
        ensure_password(api, su_user, su_pass, su_pass)
        api.cookies.clear()
        login(api, SYSTEM_ORG, su_user, su_pass)
        print(f"2. tạo tổ chức {org_code}")
        made = api.post("/api/admin/orgs", {"code": org_code, "name": "Trung tâm A", "admin_username": org_user,
                                            "admin_full_name": "Quản trị trung tâm"})
        temp = made["admin"]["temp_password"]
        print("   xong · chuyên đề, môn và nhãn mẫu đã được seed cùng tổ chức")
        print(f"3. đăng nhập {org_user} và đặt lại mật khẩu theo .ai/credentials.env")
        api.cookies.clear()
        login(api, org_code, org_user, temp)
        ensure_password(api, org_user, temp, org_pass)
        api.cookies.clear()
    login(api, org_code, org_user, org_pass)

    if not args.no_model and not args.skip_org:
        print("4. đăng ký model phân loại")
        register_model(api, f"Ollama {args.model}", args.model,
                       os.environ.get("OLLAMA_URL") or dotenv.get("OLLAMA_URL", "http://host.docker.internal:11434"))

    if args.papers:
        papers = sorted(p for p in pathlib.Path(args.papers).rglob("*.docx") if not p.name.startswith("~$"))
        if not papers:
            sys.exit(f"không thấy .docx nào trong {args.papers}")
        print(f"5. upload {len(papers)} đề")
        ids = upload_papers(api, papers)
        print("6. chờ worker tách đề (mỗi đề vài phút)")
        final = wait_for(api, ids)
        bad = {i: s for i, s in final.items() if s != "parsed"}
        if bad:
            print(f"  ⚠ {len(bad)} đề không ở trạng thái parsed: {sorted(set(bad.values()))}")
    print("xong.")
    status(api)


if __name__ == "__main__":
    main()
