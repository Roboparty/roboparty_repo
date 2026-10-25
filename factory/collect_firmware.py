#!/usr/bin/env python3
"""Collect firmware files from the repositories in firmware-manifest.json."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def git(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )


def git_output(*args: str, cwd: Path | None = None) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=cwd,
        text=True,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    ).strip()


def clone_at_ref(repository: str, ref: str, destination: Path) -> str:
    token = os.environ.get("GH_TOKEN", "")
    if token:
        url = f"https://x-access-token:{token}@github.com/{repository}.git"
    else:
        url = f"https://github.com/{repository}.git"

    git("init", "--quiet", str(destination))
    git("-C", str(destination), "remote", "add", "origin", url)
    git("-C", str(destination), "fetch", "--depth=1", "origin", ref)
    git("-C", str(destination), "checkout", "--detach", "--quiet", "FETCH_HEAD")
    return git_output("-C", str(destination), "rev-parse", "HEAD")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect(manifest_path: Path, output_dir: Path, version: str) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    firmware_root = output_dir / "firmware"
    sources = []
    seen = set()

    for source in manifest["sources"]:
        category = source["category"]
        repository = source["repository"]
        ref = source["ref"]
        patterns = source["patterns"]

        with tempfile.TemporaryDirectory(prefix=f"factory-{category}-") as temp:
            repo_dir = (Path(temp) / "repo").resolve()
            commit = clone_at_ref(repository, ref, repo_dir)

            matched = []
            for pattern in patterns:
                matched.extend(
                    path for path in repo_dir.glob(pattern) if path.is_file()
                )
            matched = sorted(set(matched), key=lambda path: str(path).lower())
            if not matched:
                raise SystemExit(
                    f"{category}: no firmware matched {patterns} at "
                    f"{repository}@{ref}"
                )

            destination_dir = firmware_root / category
            destination_dir.mkdir(parents=True, exist_ok=True)
            files = []

            for path in matched:
                name = path.name
                key = (category, name)
                if key in seen:
                    raise SystemExit(f"duplicate firmware: {category}/{name}")
                seen.add(key)

                destination = destination_dir / name
                shutil.copy2(path, destination)
                relative_source = path.relative_to(repo_dir).as_posix()
                files.append(
                    {
                        "name": name,
                        "source_path": relative_source,
                        "size": destination.stat().st_size,
                        "sha256": sha256(destination),
                    }
                )

            sources.append(
                {
                    "category": category,
                    "repository": repository,
                    "ref": ref,
                    "commit": commit,
                    "files": files,
                }
            )

    bundle_manifest = {
        "bundle": {
            "name": manifest["name"],
            "version": version,
            "created_utc": datetime.now(timezone.utc).isoformat(),
        },
        "sources": sources,
    }

    manifest_output = output_dir / "manifest.json"
    manifest_output.write_text(
        json.dumps(bundle_manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    checksum_lines = []
    for path in sorted(firmware_root.rglob("*")):
        if path.is_file():
            checksum_lines.append(
                f"{sha256(path)}  {path.relative_to(output_dir).as_posix()}"
            )
    checksum_lines.append(
        f"{sha256(manifest_output)}  {manifest_output.relative_to(output_dir).as_posix()}"
    )
    (output_dir / "SHA256SUMS").write_text(
        "\n".join(checksum_lines) + "\n",
        encoding="utf-8",
    )

    return bundle_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("factory/firmware-manifest.json"),
    )
    parser.add_argument("--output", type=Path, default=Path("dist"))
    parser.add_argument("--version", default="0.0.0")
    args = parser.parse_args()

    bundle = collect(args.manifest, args.output, args.version)
    print(f"bundle: {bundle['bundle']['name']} {bundle['bundle']['version']}")
    for source in bundle["sources"]:
        print(f"{source['category']}: {len(source['files'])} file(s)")
        for item in source["files"]:
            print(f"  {item['name']}  {item['sha256']}")
    print(f"output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
