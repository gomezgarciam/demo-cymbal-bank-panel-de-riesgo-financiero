#!/usr/bin/env python3
"""Escáner estático preventivo de secretos, API keys y credenciales para Git y CI."""

from __future__ import annotations

import os
import re
import subprocess
import sys

FORBIDDEN_FILENAMES = (
    re.compile(r"(^|/)\.env(\..+)?$"),
    re.compile(r"(^|/).*\.tfvars$"),
    re.compile(r"(^|/).*(service[-_]?account|credentials).*\.json$", re.IGNORECASE),
    re.compile(r"(^|/).*\.(pem|key|p12|pfx|jks)$", re.IGNORECASE),
)

ALLOWED_EXAMPLES = (".env.example", ".tfvars.example")

SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "GCP_API_KEY": re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
    "GITHUB_TOKEN": re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{20,}\b"),
    "GITHUB_PAT_FINE": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}\b"),
    "AWS_ACCESS_KEY": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "PRIVATE_KEY_HEADER": re.compile(r"-----BEGIN (RSA |EC |DSA |OPENSSH |)PRIVATE KEY-----"),
    "GCP_SERVICE_ACCOUNT_JSON": re.compile(r'"type"\s*:\s*"service_account"'),
    "HARDCODED_BEARER_JWT": re.compile(r"Bearer\s+eyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}"),
    "GENERIC_ASSIGNED_SECRET": re.compile(
        r"(?i)\b(api[_-]?key|secret[_-]?key|client[_-]?secret|access[_-]?token|db[_-]?password)\s*[:=]\s*['\"](?!REPLACE_WITH|changeme|dummy|test)[A-Za-z0-9_\-/+=]{16,}['\"]"
    ),
}

BINARY_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".pdf",
    ".zip",
}


def get_tracked_files() -> list[str]:
    out = subprocess.check_output(["git", "ls-files"], text=True)
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    files = get_tracked_files()
    violations: list[str] = []

    for rel_path in files:
        if any(rel_path.endswith(ex) for ex in ALLOWED_EXAMPLES):
            continue

        for fname_pat in FORBIDDEN_FILENAMES:
            if fname_pat.search(rel_path):
                violations.append(f"[FORBIDDEN_FILE] {rel_path}")

        _, ext = os.path.splitext(rel_path.lower())
        if ext in BINARY_EXTENSIONS or rel_path == "scripts/scan_secrets.py":
            continue

        if not os.path.isfile(rel_path):
            continue

        with open(rel_path, encoding="utf-8", errors="ignore") as f:
            for lineno, line in enumerate(f, start=1):
                for rule_name, pattern in SECRET_PATTERNS.items():
                    if pattern.search(line):
                        violations.append(f"[{rule_name}] {rel_path}:{lineno}")

    if violations:
        print("ERROR: Se detectaron posibles credenciales o archivos sensibles:")
        for v in violations:
            print(f"  - {v}")
        return 1

    print(f"OK: {len(files)} archivos auditados — cero API keys, tokens o secretos detectados.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
