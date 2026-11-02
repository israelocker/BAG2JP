"""Inventory/check owned Markdown without fetching links or executing examples.

Structural validation is not fact checking. JSON reports retain per-file hashes,
headings, commands and issues for a separate evidence audit. No dependency beyond
the standard library; no game settings, Git index or Markdown files are changed.
"""
import argparse
import ast
from datetime import datetime
import hashlib
import json
import logging
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

LOGGER = logging.getLogger(__name__)
EXCLUDED = {".git", "_work", "assets", "releases", "ghidra", "node_modules",
            "third_party", "__pycache__", ".venv", "psxrecomp", "recomp-ui"}
REQUIRED_FIELDS = {"id", "title", "tags", "summary", "related", "created", "updated"}
CONTEXT_SETS = {
    "startup": ["AGENTS.md", "NOTES.md", "_work/current-state.json"],
    "import_start": ["AGENTS.md", "NOTES.md", "_work/current-state.json", "IMPORT_STANDARD.md"],
}


def inventory(root: Path) -> list[str]:
    """List owned Markdown, including hidden own config but excluding generated trees."""
    if not root.is_dir():
        raise ValueError(f"Not a directory: {root}")
    paths = []
    for directory, folders, files in os.walk(root, followlinks=False):
        folders[:] = sorted(name for name in folders if name not in EXCLUDED
                            and not name.startswith("build")
                            and not (Path(directory) / name).is_symlink())
        for name in files:
            path = Path(directory) / name
            if path.suffix.lower() in {".md", ".mdx"} and not path.is_symlink():
                paths.append(path.relative_to(root).as_posix())
    return sorted(paths)


def frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Read scalar keys; JSON/Python-style arrays are parsed separately, not full YAML."""
    match = re.match(r"\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)", text, re.S)
    if not match:
        return {}, text
    fields = {}
    for line in match[1].splitlines():
        item = re.match(r"^([\w-]+):\s*(.*?)\s*$", line)
        if item:
            fields[item[1]] = item[2]
    return fields, text[match.end():]


def scalar(value: str) -> str:
    """Strip simple quoted scalars used by the local frontmatter convention."""
    return value.strip().strip('\"\'')


def body_parts(body: str) -> tuple[str, list[str], bool]:
    """Separate prose/examples with fence-aware handling of nested Markdown samples."""
    prose, examples = [], []
    marker = ""
    length = 0
    for line in body.splitlines():
        fence = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)
        if fence:
            chars, suffix = fence.groups()
            if not marker:
                marker, length = chars[0], len(chars)
            elif chars[0] == marker and len(chars) >= length and not suffix.strip():
                marker = ""
            continue
        (examples if marker else prose).append(line)
    return "\n".join(prose), examples, bool(marker)


def local_target(target: str) -> str | None:
    """Ignore remote URLs, templates, globs and local anchors without opening them."""
    target = target.strip()
    if any(char in target for char in "<>*?{}"):
        return None
    if not target or target.startswith("#"):
        return None
    if re.match(r"^[A-Za-z]:[/\\]", target):
        return None  # environment-specific references are reviewed manually
    if urlsplit(target).scheme:
        return None
    return unquote(target.split("#", 1)[0])


def inspect_document(root: Path, path: Path) -> dict:
    """Inspect structure and local references; never certify an assertion as true."""
    raw = path.read_bytes()
    text = raw.decode("utf-8-sig")
    fields, body = frontmatter(text)
    prose, examples, unclosed = body_parts(body)
    relative = path.relative_to(root).as_posix()
    historical = "/archive/" in f"/{relative}"
    specialized = path.name in {"AGENTS.md", "SKILL.md"} or relative.startswith(".opencode/")
    kind = "historical" if historical else scalar(fields.get("doc_kind", "requirements" if specialized else "unclassified"))
    issues = []

    def issue(code: str, message: str, severity: str = "error") -> None:
        issues.append({"code": code, "message": message, "severity": severity})

    if unclosed:
        issue("unclosed-fence", "Unclosed code fence", "warning" if historical else "error")
    # Harness files use specialized schemas; historical text is preserved, not relinted.
    if not historical and not specialized and "templates/" not in relative:
        missing = sorted(REQUIRED_FIELDS - fields.keys())
        if missing:
            issue("metadata", "Missing fields: " + ", ".join(missing))
        for key in REQUIRED_FIELDS & fields.keys():
            value = scalar(fields[key])
            if not value:
                issue("metadata-value", f"Empty {key}")
                continue
            if key in {"tags", "related"}:
                try:
                    array = ast.literal_eval(fields[key])
                    if not isinstance(array, list) or not all(isinstance(item, str) and item.strip() for item in array):
                        raise ValueError("expected an array of nonempty strings")
                except (ValueError, SyntaxError) as exc:
                    issue("metadata-value", f"Invalid {key}: {exc}")
            elif key in {"created", "updated"}:
                try:
                    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}(?:T.*)?", value):
                        raise ValueError("expected ISO date or timestamp")
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError as exc:
                    issue("metadata-value", f"Invalid {key}: {exc}")
    for target in re.findall(r"!?\[[^\]\n]*\]\(([^)\n]+)\)", prose):
        target = local_target(target)
        if target is not None:
            destination = root / target.lstrip("/") if target.startswith("/") else path.parent / target
            if not destination.exists():
                issue("missing-link", target, "warning" if historical or target.startswith("_work/") else "error")
    for target in re.findall(r"(?<!`)`((?:tools|docs|notes|plans|agent-skills)/[^`\s]+\.(?:md|py|ps1|sh|json))`(?!`)", prose):
        target = local_target(target)
        if target is not None and not (root / target).exists():
            issue("missing-literal", target, "warning" if historical else "error")
    if "related" in fields:
        try:
            related = ast.literal_eval(fields["related"])
            if not isinstance(related, list) or not all(isinstance(item, str) for item in related):
                raise ValueError("related must be an array of strings")
            for target in related:
                if local_target(target) is not None and not (root / target).exists():
                    issue("missing-related", target, "warning" if historical else "error")
        except (ValueError, SyntaxError) as exc:
            issue("metadata", f"Invalid related: {exc}", "warning")
    if kind == "digest" and not historical and not all(scalar(fields.get(key, "")) for key in ("source", "source_sha256")):
        issue("digest-provenance", "A digest requires source and source_sha256")
    if "source" in fields and "source_sha256" in fields and not historical:
        source = (root / scalar(fields["source"])).resolve()
        if not source.is_relative_to(root.resolve()):
            issue("source-outside-root", fields["source"])
        elif not source.is_file():
            issue("missing-source", str(source.relative_to(root)))
        elif hashlib.sha256(source.read_bytes()).hexdigest() != scalar(fields["source_sha256"]):
            issue("stale-digest", fields["source"])
    return {"path": relative, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "kind": kind, "fields": fields,
            "headings": re.findall(r"^#{1,6} .+$", prose, re.M),
            "examples": examples, "issues": issues}


def report(root: Path) -> dict:
    """Produce auditable inventory and byte-based context measurements, not token estimates."""
    documents = [inspect_document(root, root / name) for name in inventory(root)]
    ids = {}
    for doc in documents:
        if doc["kind"] != "historical" and "templates/" not in doc["path"] and "id" in doc["fields"]:
            ids.setdefault(scalar(doc["fields"]["id"]), []).append(doc["path"])
    duplicates = {key: paths for key, paths in ids.items() if len(paths) > 1}
    contexts = {}
    for name, members in CONTEXT_SETS.items():
        contexts[name] = {"files": members,
                          "bytes": sum((root / p).stat().st_size for p in members if (root / p).is_file()),
                          "missing": [p for p in members if not (root / p).is_file()]}
    issues = [issue for doc in documents for issue in doc["issues"]]
    return {"schema": 1, "root": str(root), "document_count": len(documents),
            "total_bytes": sum(doc["bytes"] for doc in documents),
            "active_bytes": sum(doc["bytes"] for doc in documents if doc["kind"] != "historical"),
            "errors": sum(i["severity"] == "error" for i in issues) + len(duplicates),
            "warnings": sum(i["severity"] == "warning" for i in issues),
            "contexts": contexts, "duplicate_ids": duplicates,
            "excluded_directory_names": sorted(EXCLUDED),
            "documents": documents}


def main() -> int:
    """Print compact results; optional --output retains the full report outside context."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("inventory", "check"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output and args.output.suffix.lower() != ".json":
        parser.error("--output must name a JSON report, not a Markdown/source file")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    try:
        result = report(args.root.resolve())
    except (OSError, UnicodeError, ValueError) as exc:
        LOGGER.error("Documentation audit failed: %s", exc)
        return 2
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    LOGGER.info(json.dumps({key: value for key, value in result.items() if key != "documents"}, ensure_ascii=False))
    return int(args.action == "check" and (result["errors"] > 0 or result["document_count"] == 0))


if __name__ == "__main__":
    raise SystemExit(main())
