"""Mirror commit timestamps from a work repo to a personal GitHub repo as empty commits.

Only dates are copied. The source repo is only read (`git fetch` + `git log`).
Usage:
  python sync_contributions.py --source PATH --target-url URL --author-email WORK_EMAIL \
      --email PERSONAL_EMAIL [--name NAME] [--branch main] [--no-push]
"""
import argparse
import os
import subprocess
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MIRROR_DIR = os.path.join(BASE_DIR, "mirror")
STATE_FILE = os.path.join(MIRROR_DIR, ".synced_shas")


def git(args, cwd, env=None, capture=False):
    return subprocess.run(
        ["git", *args], cwd=cwd, env=env, check=True, text=True,
        stdout=subprocess.PIPE if capture else None,
    ).stdout


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", required=True, help="Local clone of the work repo")
    p.add_argument("--target-url", required=True, help="Personal mirror repo URL")
    p.add_argument("--author-email", required=True, help="Email on your commits in the source repo")
    p.add_argument("--email", required=True, help="Email verified on your personal GitHub account")
    p.add_argument("--name", default="mirror")
    p.add_argument("--branch", default="main")
    p.add_argument("--no-push", action="store_true")
    a = p.parse_args()

    git(["fetch", "origin", a.branch], a.source)  # does not modify the working tree
    out = git(["log", f"origin/{a.branch}", "--reverse", f"--author={a.author_email}",
               "--pretty=format:%H|%aI"], a.source, capture=True)
    lines = [l.split("|") for l in out.splitlines() if l]

    os.makedirs(MIRROR_DIR, exist_ok=True)
    if not os.path.isdir(os.path.join(MIRROR_DIR, ".git")):
        git(["init", "-b", "main"], MIRROR_DIR)
        git(["remote", "add", "origin", a.target_url], MIRROR_DIR)
    git(["config", "user.email", a.email], MIRROR_DIR)
    git(["config", "user.name", a.name], MIRROR_DIR)

    done = set()
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            done = {l.strip() for l in f if l.strip()}

    new = [l for l in lines if l[0] not in done]
    with open(STATE_FILE, "a") as state:
        for sha, date in new:
            env = {**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
            git(["commit", "--allow-empty", "-q", "-m", f"Sync contribution {sha[:7]}"], MIRROR_DIR, env=env)
            state.write(sha + "\n")
            state.flush()
    print(f"Created {len(new)} commit(s).")

    if not a.no_push:
        git(["push", "-u", "origin", "main"], MIRROR_DIR)
        print("Pushed to", a.target_url)


if __name__ == "__main__":
    sys.exit(main())
