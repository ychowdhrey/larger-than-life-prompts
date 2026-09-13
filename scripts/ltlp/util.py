"""Filesystem, hashing and small shared helpers."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from typing import Any


class ImmutableWriteError(RuntimeError):
    """Raised when something tries to overwrite a raw output that already exists."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def write_json(path: str, obj: Any, *, sort_keys: bool = False) -> None:
    """Atomic write. Overwrites freely; use write_json_once for raw outputs."""
    ensure_dir(os.path.dirname(path) or ".")
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(obj, fh, indent=2, ensure_ascii=False, sort_keys=sort_keys)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_text(path: str, text: str) -> None:
    ensure_dir(os.path.dirname(path) or ".")
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def write_json_once(path: str, obj: Any) -> str:
    """Write-once. Refuses to touch an existing file.

    Raw generations and judgments are written through this function so that a resumed or
    repeated run can never silently rewrite a sample that has already been produced.
    Returns the sha256 of the bytes written.
    """
    if os.path.exists(path):
        raise ImmutableWriteError(
            "refusing to overwrite existing raw output: %s" % path)
    ensure_dir(os.path.dirname(path) or ".")
    payload = json.dumps(obj, indent=2, ensure_ascii=False) + "\n"
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path) or ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(payload)
        # O_EXCL-style final guard against a concurrent writer.
        if os.path.exists(path):
            os.unlink(tmp)
            raise ImmutableWriteError(
                "refusing to overwrite existing raw output: %s" % path)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return sha256_text(payload)


def append_jsonl(path: str, obj: Any) -> None:
    ensure_dir(os.path.dirname(path) or ".")
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, sort_keys=True) + "\n")


def read_jsonl(path: str) -> list:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def extract_json_object(text: str) -> dict:
    """Pull the first complete JSON object out of a model response.

    Judges are asked for bare JSON, but a fenced block or a sentence of preamble is a
    normal failure mode and should not cost a judgment.
    """
    if text is None:
        raise ValueError("no text to parse")
    stripped = text.strip()
    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict):
            return obj
    except json.JSONDecodeError:
        pass
    fence = re.search(r"```(?:json)?\s*(.+?)```", stripped, re.DOTALL)
    candidates = []
    if fence:
        candidates.append(fence.group(1).strip())
    start = stripped.find("{")
    while start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(stripped)):
            ch = stripped[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(stripped[start:i + 1])
                    break
        break
    for cand in candidates:
        try:
            obj = json.loads(cand)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    raise ValueError("no JSON object found in response")


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text or ""))
