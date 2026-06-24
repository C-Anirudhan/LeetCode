from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote


PROBLEM_RE = re.compile(r"^\d{4}-[a-z0-9]+(?:-[a-z0-9]+)*$")
TITLE_RE = re.compile(r"<h2[^>]*>.*?<a[^>]*>(.*?)</a>.*?</h2>", re.I | re.S)
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
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
IGNORED_ROOT_DIRS = {".git", "automation", "extension", "__pycache__"}


class StatsError(Exception):
    pass


def run(args: list[str], root: Path) -> str:
    result = subprocess.run(args, cwd=root, text=True, capture_output=True)
    if result.returncode:
        output = "\n".join(part for part in (result.stdout.strip(), result.stderr.strip()) if part)
        raise StatsError(f"{' '.join(args)} failed:\n{output}")
    return result.stdout.strip()


def git_hash(root: Path, path: Path) -> str:
    return run(["git", "hash-object", path.relative_to(root).as_posix()], root)


def repository_tree_url(root: Path) -> str:
    remote = run(["git", "config", "--get", "remote.origin.url"], root)
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", remote)
    if not match:
        raise StatsError("remote.origin.url is not a GitHub repository")
    branch = run(["git", "branch", "--show-current"], root) or "main"
    return f"https://github.com/{match.group(1)}/{match.group(2)}/tree/{quote(branch, safe='')}"


def problem_dirs(root: Path) -> list[Path]:
    found: list[Path] = []
    names: dict[str, Path] = {}
    for category in sorted(root.iterdir(), key=lambda path: path.name.casefold()):
        if not category.is_dir() or category.name in IGNORED_ROOT_DIRS or category.name.startswith("."):
            continue
        for child in sorted(category.iterdir(), key=lambda path: path.name):
            if child.is_dir() and PROBLEM_RE.fullmatch(child.name):
                if child.name in names:
                    raise StatsError(
                        f"duplicate problem folder {child.name}: "
                        f"{names[child.name].relative_to(root)} and {child.relative_to(root)}"
                    )
                names[child.name] = child
                found.append(child)
    return sorted(found, key=lambda path: (int(path.name[:4]), path.name))


def solution_file(problem_dir: Path) -> Path:
    preferred = [
        path
        for path in problem_dir.iterdir()
        if path.is_file()
        and path.stem == problem_dir.name
        and path.suffix.lower() in SOLUTION_EXTENSIONS
    ]
    candidates = preferred or [
        path
        for path in problem_dir.iterdir()
        if path.is_file() and path.suffix.lower() in SOLUTION_EXTENSIONS
    ]
    if len(candidates) != 1:
        names = ", ".join(sorted(path.name for path in candidates)) or "none"
        raise StatsError(f"{problem_dir.name}: expected one solution file, found {names}")
    return candidates[0]


def problem_title(problem_dir: Path) -> str:
    readme = problem_dir / "README.md"
    if readme.is_file():
        match = TITLE_RE.search(readme.read_text(encoding="utf-8", errors="replace"))
        if match:
            title = html.unescape(re.sub(r"<[^>]+>", "", match.group(1))).strip()
            title = re.sub(r"^\d+\.\s*", "", title)
            if title:
                return title
    words = problem_dir.name[5:].replace("-", " ").title()
    return words.replace(" Ii", " II").replace(" Iii", " III")


def render_readme(root: Path, problems: list[Path]) -> str:
    base_url = repository_tree_url(root)
    grouped: dict[str, list[Path]] = {}
    for problem in problems:
        grouped.setdefault(problem.parent.name, []).append(problem)

    lines = [
        "# LeetCode",
        "",
        f"A collection of {len(problems)} solved LeetCode questions, organized by primary algorithm category.",
    ]
    for category in sorted(grouped, key=str.casefold):
        lines.extend(["", f"## {category}", "", "| Problem |", "| --- |"])
        for problem in sorted(grouped[category], key=lambda path: (int(path.name[:4]), path.name)):
            encoded = "/".join(quote(part, safe="") for part in problem.relative_to(root).parts)
            number = problem.name[:4]
            lines.append(f"| [{number} - {problem_title(problem)}]({base_url}/{encoded}) |")
    return "\n".join(lines) + "\n"


def load_stats(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StatsError(f"could not read stats.json: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("leetcode"), dict):
        raise StatsError("stats.json must contain a leetcode object")
    return data


def difficulty_for(
    problem: Path,
    old_shas: dict[str, Any],
    override_problem: str | None,
    override_difficulty: str | None,
    write: bool,
) -> str:
    if problem.name == override_problem:
        return str(override_difficulty)
    old_entry = old_shas.get(problem.name, {})
    difficulty = old_entry.get("difficulty") if isinstance(old_entry, dict) else None
    if difficulty in VALID_DIFFICULTIES:
        return difficulty
    if not write:
        raise StatsError(f"{problem.name}: difficulty is missing or invalid")
    if not sys.stdin.isatty():
        raise StatsError(
            f"{problem.name}: difficulty is missing; rerun with "
            "--problem, --difficulty, and --algorithm"
        )
    while True:
        answer = input(f"Difficulty for {problem.name} (easy/medium/hard): ").strip().lower()
        if answer in VALID_DIFFICULTIES:
            return answer


def expected_stats(
    root: Path,
    data: dict[str, Any],
    problems: list[Path],
    override_problem: str | None,
    override_difficulty: str | None,
    write: bool,
) -> dict[str, Any]:
    old_leetcode = data["leetcode"]
    old_shas = old_leetcode.get("shas", {})
    if not isinstance(old_shas, dict):
        old_shas = {}

    shas: dict[str, Any] = {}
    counts = {"easy": 0, "medium": 0, "hard": 0}
    for problem in problems:
        readme = problem / "README.md"
        if not readme.is_file():
            raise StatsError(f"{problem.name}: README.md was not found")
        solution = solution_file(problem)
        difficulty = difficulty_for(
            problem, old_shas, override_problem, override_difficulty, write
        )
        counts[difficulty] += 1
        shas[problem.name] = {
            solution.name: git_hash(root, solution),
            "README.md": git_hash(root, readme),
            "difficulty": difficulty,
        }

    root_readme = root / "README.md"
    shas["README.md"] = {"": git_hash(root, root_readme)}
    old_self = old_shas.get("stats.json")
    if isinstance(old_self, dict):
        shas["stats.json"] = old_self

    return {
        **data,
        "leetcode": {
            **old_leetcode,
            "easy": counts["easy"],
            "hard": counts["hard"],
            "medium": counts["medium"],
            "shas": shas,
            "solved": len(problems),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check or update README.md and stats.json from categorized problem folders."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    parser.add_argument("--problem")
    parser.add_argument("--difficulty", choices=sorted(VALID_DIFFICULTIES))
    parser.add_argument("--algorithm")
    args = parser.parse_args()
    supplied = (args.problem is not None, args.difficulty is not None, args.algorithm is not None)
    if any(supplied) and not all(supplied):
        parser.error("--problem, --difficulty, and --algorithm must be used together")
    if any(supplied) and not args.write:
        parser.error("problem overrides can only be used with --write")
    return args


def main() -> int:
    args = parse_args()
    root = Path(__file__).resolve().parent
    stats_path = root / "stats.json"
    readme_path = root / "README.md"

    try:
        problems = problem_dirs(root)
        if args.problem:
            target = root / args.algorithm / args.problem
            if target not in problems:
                raise StatsError(
                    f"{args.problem} was not found under algorithm folder {args.algorithm}"
                )

        expected_readme = render_readme(root, problems)
        current_readme = readme_path.read_text(encoding="utf-8")
        readme_changed = current_readme != expected_readme
        if args.write and readme_changed:
            readme_path.write_text(expected_readme, encoding="utf-8")

        current_stats = load_stats(stats_path)
        expected = expected_stats(
            root,
            current_stats,
            problems,
            args.problem,
            args.difficulty,
            args.write,
        )
        stats_changed = current_stats != expected

        if args.check:
            changes = []
            if readme_changed:
                changes.append("README.md is out of date")
            if stats_changed:
                changes.append("stats.json is out of date")
            if changes:
                raise StatsError("; ".join(changes))
            print("README.md and stats.json are up to date.")
            return 0

        if stats_changed:
            stats_path.write_text(
                json.dumps(expected, separators=(",", ":"), ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        changed = [name for name, value in (("README.md", readme_changed), ("stats.json", stats_changed)) if value]
        print(f"Updated {', '.join(changed)}." if changed else "README.md and stats.json are already up to date.")
        return 0
    except StatsError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
