"""Stage 1, items 1-2: tag selection and the standard Docker build of the spec (single-page HTML + validusage.json).

The build runs in a named Docker volume (ext4 inside the docker-desktop WSL VM), not under /mnt/c.
Outputs are copied into data/build/ and their sha256 is recorded in data/build/build_info.json.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from vkrag.config import BUILD, RAW, load_config, save_config_value

DOCS = RAW / "Vulkan-Docs"
HEADERS = RAW / "Vulkan-Headers"
DOCS_URL = "https://github.com/KhronosGroup/Vulkan-Docs.git"
TAG_RE = re.compile(r"^v1\.4\.\d+$")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def list_tags(repo: Path) -> list[tuple[str, dt.date]]:
    out = _git(repo, "for-each-ref", "--sort=-creatordate", "--format=%(refname:short) %(creatordate:short)", "refs/tags")
    res = []
    for line in out.splitlines():
        name, date = line.split()
        if TAG_RE.match(name):
            res.append((name, dt.date.fromisoformat(date)))
    return res


def pinned_image_digest(tag: str) -> str | None:
    """Image digest pinned in BUILD.adoc of the tag itself."""
    text = _git(DOCS, "show", f"{tag}:BUILD.adoc")
    m = re.search(r"khronosgroup/docker-images@(sha256:[0-9a-f]{64})", text)
    return m.group(1) if m else None


def select_tag(write: bool = True) -> str:
    cfg = load_config()
    freeze = dt.date.fromisoformat(cfg["spec"]["freeze_date"])
    limit = freeze - dt.timedelta(days=cfg["spec"]["min_tag_age_days"])
    headers_tags = {t for t, _ in list_tags(HEADERS)}
    for tag, date in list_tags(DOCS):
        if date <= limit and tag in headers_tags:
            digest = pinned_image_digest(tag)
            print(f"tag={tag} date={date} (limit {limit}); pinned image digest={digest}")
            if write:
                save_config_value("spec.tag", tag)
                if digest:
                    save_config_value("spec.docker_digest", digest)
            return tag
    raise SystemExit("no suitable tag")


def _docker(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    print("+ docker", " ".join(args))
    return subprocess.run(["docker", *args], check=check)


def build(jobs: int | None = None) -> None:
    cfg = load_config()
    tag, digest, vol = cfg["spec"]["tag"], cfg["spec"]["docker_digest"], cfg["spec"]["docker_volume"]
    if not tag or not digest:
        raise SystemExit("run `vkrag spec select-tag` first")
    image = f"khronosgroup/docker-images@{digest}"
    jobs = jobs or os.cpu_count() or 4
    _docker("volume", "create", vol)
    script = f"""
set -euo pipefail
cd /vk
if [ ! -d Vulkan-Docs/.git ]; then git -c core.autocrlf=false clone --quiet {DOCS_URL} Vulkan-Docs; fi
cd Vulkan-Docs
git fetch --quiet --tags origin
git checkout --quiet --force {tag}
git clean -fdxq
./makeSpec -spec all -j {jobs} -O html validusage
ls -la gen/out/html/vkspec.html gen/out/validation/validusage.json
"""
    _docker("run", "--rm", "-v", f"{vol}:/vk", image, "bash", "-c", script)

    BUILD.mkdir(parents=True, exist_ok=True)
    cname = "vkrag-spec-copy"
    _docker("rm", "-f", cname, check=False)
    _docker("create", "--name", cname, "-v", f"{vol}:/vk", image)
    try:
        for src, dst in [
            ("/vk/Vulkan-Docs/gen/out/html/vkspec.html", BUILD / "vkspec.html"),
            ("/vk/Vulkan-Docs/gen/out/validation/validusage.json", BUILD / "validusage.json"),
            # attributes defined by the -spec all build (used to evaluate ifdefs in adoc_conditions)
            ("/vk/Vulkan-Docs/gen/specattribs.adoc", BUILD / "specattribs.adoc"),
        ]:
            _docker("cp", f"{cname}:{src}", str(dst))
    finally:
        _docker("rm", "-f", cname, check=False)

    info = {
        "tag": tag,
        "docker_image": image,
        "built_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "docs_commit": _git(DOCS, "rev-list", "-n1", tag).strip(),
        "files": {p.name: sha256(p) for p in [BUILD / "vkspec.html", BUILD / "validusage.json", BUILD / "specattribs.adoc"]},
    }
    (BUILD / "build_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    print(json.dumps(info, indent=2))
