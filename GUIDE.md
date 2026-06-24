# Repository Guide

Each solved problem belongs to one primary algorithm category.

```text
Algorithm Category/
  0001-problem-name/
    0001-problem-name.py
    README.md
```

When adding a solution:

1. Choose its primary algorithm category.
2. Create a folder named `problem-number-problem-slug`.
3. Keep the solution and problem `README.md` together in that folder.
4. Add the problem link to the matching category in the root `README.md`.
5. Keep `stats.json` counts and hashes synchronized.

If a problem fits several categories, place it under the category that best represents the submitted solution.

## Automatic LeetCode Sync

This repository includes the same local browser automation used for the BibinSanju
repository. It consists of:

- `extension/`: an unpacked Chrome/Edge extension shown on LeetCode problem pages.
- `automation/local_leetcode_server.py`: a loopback-only helper that writes and commits solutions.
- `sync_stats.py`: regenerates the root problem list and keeps `stats.json` synchronized.

Start the local helper from the repository root:

```powershell
python automation/local_leetcode_server.py
```

The helper prints a local token. Keep that terminal open.

To install the extension:

1. Open `chrome://extensions` or `edge://extensions`.
2. Enable Developer mode.
3. Choose **Load unpacked** and select this repository's `extension` folder.
4. Open the extension popup, paste the token printed by the helper, and click **Test server**.

On a LeetCode problem page, submit the solution and click **Save to Local Repo**.
Review the detected problem data, primary algorithm, code, README content, performance
commit message, and preview. Then click **Save and commit**.

The helper binds only to `127.0.0.1`, requires the generated token, writes the problem
under the selected algorithm category, updates `README.md` and `stats.json`, validates
them, stages only those files, and creates the commit.

## Stats Commands

Check without editing:

```powershell
python sync_stats.py --check
```

Synchronize existing problems:

```powershell
python sync_stats.py --write
```

Register a new categorized problem manually:

```powershell
python sync_stats.py --write --problem 0002-add-two-numbers --difficulty medium --algorithm "Linked List"
```
