#!/usr/bin/env python3
"""Read original-PDF page ranges from the bundled transcription; verify snapshots."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "references" / "sources"


def verify():
    manifest = json.loads((SOURCES / "manifest.json").read_text(encoding="utf-8"))
    for entry in manifest["files"]:
        path = (SOURCES / entry["file"]).resolve()
        if not path.is_relative_to(SOURCES.resolve()):
            raise ValueError("快照清单路径超出来源目录")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise ValueError(f"来源快照校验失败：{entry['file']}")
    print(f"来源快照校验通过：{len(manifest['files'])}份文件；{manifest['model_version']}")


def parse_pages(spec):
    pages = set()
    for part in spec.split(","):
        match = re.fullmatch(r"\s*(\d+)(?:\s*-\s*(\d+))?\s*", part)
        if not match:
            raise ValueError(f"无效页码：{part}")
        start, end = int(match[1]), int(match[2] or match[1])
        if not 1 <= start <= end <= 313:
            raise ValueError("页码应在1–313内，起始页不能大于结束页")
        pages.update(range(start, end + 1))
    return sorted(pages)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--pages", help="原PDF页码，例如14,20,29-34")
    mode.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        if args.verify:
            verify()
            return
        document = (SOURCES / "product-de-model.md").read_text(encoding="utf-8")
        matches = list(re.finditer(r'<a id="pdf-page-(\d+)"></a>', document))
        spans = {int(m[1]): document[m.start(): matches[i+1].start() if i+1 < len(matches) else len(document)] for i, m in enumerate(matches)}
        selected = parse_pages(args.pages)
        if any(p not in spans for p in selected):
            raise ValueError("阅读版缺少所请求的原PDF页锚点")
        for page in selected:
            print(spans[page].rstrip(), end="\n\n")
    except (OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
