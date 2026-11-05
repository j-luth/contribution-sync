"""Mirror commit timestamps from work repos to a personal GitHub repo as empty commits.

Only commit dates are copied (no code, messages or file names), so they count on your
contribution graph. Source repos are only read (`git fetch` + `git log`).

Configuration lives in config.json next to this script (see config.example.json).

Usage:
  python sync_contributions.py                  # sync all configured repos
  python sync_contributions.py --repo NAME      # sync only one repo
  python sync_contributions.py --add PATH [--branch main] [--name NAME]
  python sync_contributions.py --list
  python sync_contributions.py --no-push
"""
import argparse
import json
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
MIRROR_DIR = os.path.join(BASE_DIR, "mirror")
STATE_FILE = os.path.join(MIRROR_DIR, ".synced_shas")


def git(args, cwd, env=None, capture=False):
    return subprocess.run(
        ["git", *args], cwd=cwd, env=env, check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
    ).stdout


def load_config():
    if not os.path.exists(CONFIG_FILE):
        sys.exit("config.json not found. Copy config.example.json to config.json and edit it.")
    with open(CONFIG_FILE) as f:
        return json.load(f)


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def add_repo(cfg, path, branch, name):
    path = os.path.abspath(path)
    if not os.path.isdir(os.path.join(path, ".git")):
        sys.exit(f"Not a git repo: {path}")
    name = name or os.path.basename(path)
    if any(r["name"] == name or r["path"] == path for r in cfg["repos"]):
        sys.exit(f"Already configured: {name}")
    cfg["repos"].append({"name": name, "path": path, "branch": branch})
    save_config(cfg)
    print(f"Added {name} ({branch}).")


def collect_commits(cfg, repo):
    git(["fetch", "origin", repo["branch"]], repo["path"])  # does not touch the working tree
    out = git(
        ["log", f"origin/{repo['branch']}", "--reverse", f"--author={cfg['author_email']}",
         "--pretty=format:%H|%aI"],
        repo["path"], capture=True,
    )
    return [l.split("|") for l in out.splitlines() if l]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", help="Only sync this repo name")
    p.add_argument("--add", metavar="PATH", help="Add a local repo to config.json and exit")
    p.add_argument("--branch", default="main", help="Branch for --add (default: main)")
    p.add_argument("--name", help="Name for --add (default: folder name)")
    p.add_argument("--list", action="store_true")
    p.add_argument("--no-push", action="store_true")
    a = p.parse_args()

    cfg = load_config()
    if a.add:
        return add_repo(cfg, a.add, a.branch, a.name)
    repos = cfg["repos"]
    if a.list:
        for r in repos:
            print(f"{r['name']}: {r['path']} [{r['branch']}]")
        return
    if a.repo:
        repos = [r for r in repos if r["name"] == a.repo]
        if not repos:
            sys.exit(f"No repo named {a.repo}. Use --list.")

    os.makedirs(MIRROR_DIR, exist_ok=True)
    if not os.path.isdir(os.path.join(MIRROR_DIR, ".git")):
        git(["init", "-b", "main"], MIRROR_DIR)
        git(["remote", "add", "origin", cfg["target_repo_url"]], MIRROR_DIR)
    git(["config", "user.email", cfg["personal_email"]], MIRROR_DIR)
    git(["config", "user.name", cfg["personal_name"]], MIRROR_DIR)

    done = set()
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            done = {l.strip() for l in f if l.strip()}

    total = 0
    with open(STATE_FILE, "a") as state:
        for repo in repos:
            new = [c for c in collect_commits(cfg, repo) if c[0] not in done]
            for sha, date in new:
                env = {**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
                git(["commit", "--allow-empty", "-q", "-m", f"Sync {repo['name']} {sha[:7]}"],
                    MIRROR_DIR, env=env)
                state.write(sha + "\n")
                state.flush()
            print(f"{repo['name']}: {len(new)} new commit(s)")
            total += len(new)
    print(f"Created {total} commit(s).")

    if not a.no_push:
        git(["push", "-u", "origin", "main"], MIRROR_DIR)
        print("Pushed to", cfg["target_repo_url"])


if __name__ == "__main__":
    sys.exit(main())
