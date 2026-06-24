from __future__ import annotations

import argparse
import json
import os
import re
import secrets
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


HOST = "127.0.0.1"
DEFAULT_PORT = 8766
TOKEN_HEADER = "X-Local-LeetCode-Token"
TOKEN_FILE = "local_leetcode_token.json"
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
PROBLEM_RE = re.compile(r"^\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOLUTION_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".cxx",
    ".go",
    ".java",
    ".js",
    ".kt",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".sql",
    ".swift",
    ".ts",
}
LANGUAGE_EXTENSIONS = {
    "c": ".c",
    "c++": ".cpp",
    "cpp": ".cpp",
    "csharp": ".cs",
    "c#": ".cs",
    "golang": ".go",
    "go": ".go",
    "java": ".java",
    "javascript": ".js",
    "javascript/typescript": ".js",
    "js": ".js",
    "kotlin": ".kt",
    "mysql": ".sql",
    "mssql": ".sql",
    "oraclesql": ".sql",
    "pandas": ".py",
    "php": ".php",
    "python": ".py",
    "python3": ".py",
    "ruby": ".rb",
    "rust": ".rs",
    "scala": ".scala",
    "swift": ".swift",
    "typescript": ".ts",
    "ts": ".ts",
}
ALGORITHM_CATEGORIES = (
    "Backtracking",
    "Basic Array and String",
    "Binary Search",
    "Bit Manipulation",
    "Dynamic Programming",
    "Graph DFS and BFS",
    "Greedy",
    "Hash Map and Frequency",
    "Heap and Priority Queue",
    "Intervals",
    "Linked List",
    "Prefix Sum and Difference Array",
    "Shortest Path and Weighted Graph",
    "Sliding Window",
    "Stack and Monotonic Stack",
    "Topological Sort and Dependency Graphs",
    "Trees and BST",
    "Trie",
    "Two Pointers",
    "Union Find - Disjoint Set Union",
)


class LocalLeetCodeError(Exception):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def run_command(args: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=root, text=True, capture_output=True)


def command_or_error(args: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    result = run_command(args, root)
    if result.returncode:
        output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        raise LocalLeetCodeError(f"{' '.join(args)} failed:\n{output}")
    return result


def load_or_create_token(root: Path) -> str:
    env_token = os.environ.get("LOCAL_LEETCODE_TOKEN", "").strip()
    if env_token:
        return env_token
    token_path = root / "automation" / TOKEN_FILE
    if token_path.is_file():
        try:
            token = str(json.loads(token_path.read_text(encoding="utf-8")).get("token", "")).strip()
        except (OSError, json.JSONDecodeError):
            token = ""
        if token:
            return token
    token = secrets.token_urlsafe(32)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(json.dumps({"token": token}, indent=2) + "\n", encoding="utf-8")
    return token


def language_extension(language: Any, lang_slug: Any) -> str:
    for raw in (lang_slug, language):
        candidate = str(raw or "").strip().lower()
        if candidate in LANGUAGE_EXTENSIONS:
            return LANGUAGE_EXTENSIONS[candidate]
    raise LocalLeetCodeError(
        f"unsupported language: {language or lang_slug}; add it to LANGUAGE_EXTENSIONS"
    )


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    problem = payload.get("problem")
    if not isinstance(problem, dict):
        raise LocalLeetCodeError("payload.problem must be an object")

    slug = str(problem.get("slug") or problem.get("titleSlug") or "").strip().lower()
    if not SLUG_RE.fullmatch(slug):
        raise LocalLeetCodeError(f"invalid LeetCode slug: {slug}")
    frontend_id = str(problem.get("frontendId") or "").strip()
    if not frontend_id.isdigit():
        raise LocalLeetCodeError("problem frontend id must be numeric")
    folder = f"{int(frontend_id):04d}-{slug}"
    if not PROBLEM_RE.fullmatch(folder):
        raise LocalLeetCodeError(f"invalid problem folder: {folder}")

    algorithm = str(payload.get("algorithm") or "").strip()
    if algorithm not in ALGORITHM_CATEGORIES:
        raise LocalLeetCodeError(
            f"algorithm must be one of: {', '.join(ALGORITHM_CATEGORIES)}"
        )
    difficulty = str(problem.get("difficulty") or "").strip().lower()
    if difficulty not in VALID_DIFFICULTIES:
        raise LocalLeetCodeError("difficulty must be easy, medium, or hard")

    code = str(payload.get("code") or "").replace("\r\n", "\n")
    readme = str(payload.get("readmeContent") or "").replace("\r\n", "\n")
    commit_message = str(payload.get("commitMessage") or "").strip()
    if not code.strip():
        raise LocalLeetCodeError("solution code cannot be empty")
    if not readme.strip():
        raise LocalLeetCodeError("README content cannot be empty")
    if not commit_message:
        raise LocalLeetCodeError("commit message cannot be empty")

    return {
        "folder": folder,
        "algorithm": algorithm,
        "difficulty": difficulty,
        "extension": language_extension(payload.get("language"), payload.get("langSlug")),
        "code": code.rstrip() + "\n",
        "readme": readme.rstrip() + "\n",
        "commitMessage": commit_message,
        "overwrite": bool(payload.get("overwrite")),
    }


def relative(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def target_dir(root: Path, normalized: dict[str, Any]) -> Path:
    return root / normalized["algorithm"] / normalized["folder"]


def existing_problem_dirs(root: Path, folder: str) -> list[Path]:
    matches: list[Path] = []
    for category in ALGORITHM_CATEGORIES:
        candidate = root / category / folder
        if candidate.is_dir():
            matches.append(candidate)
    legacy = root / folder
    if legacy.is_dir():
        matches.append(legacy)
    return matches


def existing_solutions(problem_dir: Path) -> list[Path]:
    if not problem_dir.is_dir():
        return []
    return sorted(
        (
            path
            for path in problem_dir.iterdir()
            if path.is_file() and path.suffix.lower() in SOLUTION_EXTENSIONS
        ),
        key=lambda path: path.name,
    )


def preview_payload(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_payload(payload)
    destination = target_dir(root, normalized)
    other_locations = [
        path
        for path in existing_problem_dirs(root, normalized["folder"])
        if path.resolve() != destination.resolve()
    ]
    solution_name = normalized["folder"] + normalized["extension"]
    return {
        "problemFolder": normalized["folder"],
        "algorithm": normalized["algorithm"],
        "problemPath": relative(root, destination),
        "solutionPath": relative(root, destination / solution_name),
        "readmePath": relative(root, destination / "README.md"),
        "exists": destination.exists(),
        "conflict": bool(other_locations),
        "conflictingPaths": [relative(root, path) for path in other_locations],
        "existingFiles": sorted(path.name for path in destination.iterdir())
        if destination.is_dir()
        else [],
        "difficulty": normalized["difficulty"],
        "commitMessage": normalized["commitMessage"],
    }


def write_problem(root: Path, normalized: dict[str, Any]) -> None:
    destination = target_dir(root, normalized)
    conflicts = [
        path
        for path in existing_problem_dirs(root, normalized["folder"])
        if path.resolve() != destination.resolve()
    ]
    if conflicts:
        raise LocalLeetCodeError(
            f"{normalized['folder']} already exists elsewhere: "
            + ", ".join(relative(root, path) for path in conflicts)
        )
    if destination.exists() and not normalized["overwrite"]:
        raise LocalLeetCodeError(
            f"{relative(root, destination)} already exists; confirm overwrite first"
        )

    destination.mkdir(parents=True, exist_ok=True)
    solution_name = normalized["folder"] + normalized["extension"]
    for old_solution in existing_solutions(destination):
        if old_solution.name != solution_name:
            old_solution.unlink()
    (destination / solution_name).write_text(normalized["code"], encoding="utf-8")
    (destination / "README.md").write_text(normalized["readme"], encoding="utf-8")


def sync_repository(root: Path, normalized: dict[str, Any]) -> list[str]:
    command = [
        sys.executable,
        "sync_stats.py",
        "--write",
        "--problem",
        normalized["folder"],
        "--difficulty",
        normalized["difficulty"],
        "--algorithm",
        normalized["algorithm"],
    ]
    write_result = command_or_error(command, root)
    check_result = command_or_error([sys.executable, "sync_stats.py", "--check"], root)
    return [write_result.stdout.strip(), check_result.stdout.strip()]


def commit_changes(root: Path, normalized: dict[str, Any]) -> dict[str, Any]:
    problem_path = relative(root, target_dir(root, normalized))
    pathspecs = [problem_path, "README.md", "stats.json"]
    command_or_error(["git", "add", "--", *pathspecs], root)
    diff = run_command(["git", "diff", "--cached", "--quiet", "--", *pathspecs], root)
    if diff.returncode == 0:
        return {"committed": False, "message": "No changes to commit."}
    if diff.returncode != 1:
        raise LocalLeetCodeError("git diff --cached failed")
    result = command_or_error(
        ["git", "commit", "-m", normalized["commitMessage"], "--", *pathspecs], root
    )
    return {"committed": True, "message": result.stdout.strip()}


def save_payload(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_payload(payload)
    preview = preview_payload(root, payload)
    write_problem(root, normalized)
    sync_output = sync_repository(root, normalized)
    commit = commit_changes(root, normalized)
    return {"ok": True, "preview": preview, "syncOutput": sync_output, "commit": commit}


class LocalLeetCodeHandler(BaseHTTPRequestHandler):
    server_version = "LocalLeetCodeServer/0.2"

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", f"Content-Type, {TOKEN_HEADER}")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        if urlparse(self.path).path != "/health":
            self.write_json({"ok": False, "error": "not found"}, status=404)
            return
        self.write_json(
            {
                "ok": True,
                "repoRoot": str(self.server.repo_root),
                "tokenHeader": TOKEN_HEADER,
            }
        )

    def do_POST(self) -> None:
        try:
            self.require_token()
            payload = self.read_payload()
            path = urlparse(self.path).path
            if path == "/preview":
                self.write_json(
                    {"ok": True, "preview": preview_payload(self.server.repo_root, payload)}
                )
            elif path == "/save":
                self.write_json(save_payload(self.server.repo_root, payload))
            else:
                self.write_json({"ok": False, "error": "not found"}, status=404)
        except (LocalLeetCodeError, json.JSONDecodeError) as exc:
            self.write_json({"ok": False, "error": str(exc)}, status=400)
        except Exception as exc:
            self.write_json({"ok": False, "error": f"unexpected error: {exc}"}, status=500)

    def require_token(self) -> None:
        supplied = self.headers.get(TOKEN_HEADER, "")
        if not secrets.compare_digest(supplied, self.server.token):
            raise LocalLeetCodeError("invalid or missing local token")

    def read_payload(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 5_000_000:
            raise LocalLeetCodeError("request body must be between 1 byte and 5 MB")
        payload = json.loads(self.rfile.read(length).decode("utf-8"))
        if not isinstance(payload, dict):
            raise LocalLeetCodeError("request body must be a JSON object")
        return payload

    def write_json(self, payload: dict[str, Any], *, status: int = 200) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stderr.write("local-leetcode: " + format % args + "\n")


class LocalLeetCodeServer(ThreadingHTTPServer):
    repo_root: Path
    token: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the local helper used by the Local LeetCode Sync extension."
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = repo_root()
    token = load_or_create_token(root)
    server = LocalLeetCodeServer((HOST, args.port), LocalLeetCodeHandler)
    server.repo_root = root
    server.token = token
    print(f"Local LeetCode server listening on http://{HOST}:{args.port}")
    print(f"Repo root: {root}")
    print(f"Extension token: {token}")
    print("Keep this window open while saving from LeetCode. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping local LeetCode server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
