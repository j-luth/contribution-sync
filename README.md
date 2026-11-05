# contribution-sync

Mirrors the **timestamps** of your commits from work repos (Bitbucket, GitHub, etc.) to a private
personal GitHub repo as empty commits, so your activity shows on your personal contribution graph.
No code, commit messages or file names are copied.

> Check your employer's policy before mirroring work activity.

## Setup

1. Create an empty **private** repo on your personal GitHub account (the "mirror").
2. In your profile settings, enable **Include private contributions**.
3. Make sure `personal_email` is a verified email on that GitHub account.
4. Copy `config.example.json` to `config.json` and fill it in:
   - `author_email`: the email on your commits in the source repos
   - `personal_email` / `personal_name`: identity used for the mirror commits
   - `target_repo_url`: the mirror repo (SSH URL recommended)
   - `repos`: local clones to mirror (or use `--add`)
5. Auth to the mirror: add an SSH deploy key (write access) to the mirror repo and point the
   `mirror/` repo at it, e.g. `git -C mirror config core.sshCommand "ssh -i ~/.ssh/KEY -o IdentitiesOnly=yes"`.
   This keeps it separate from any other GitHub account you're signed in to.

`config.json` and `mirror/` are git-ignored.

## Usage

```
python sync_contributions.py                 # sync all repos
python sync_contributions.py --repo NAME     # sync one repo
python sync_contributions.py --add PATH [--branch main] [--name NAME]
python sync_contributions.py --list
python sync_contributions.py --no-push       # create commits without pushing
```

Run it whenever new commits land on the tracked branches. Only commits not yet mirrored are added.

## What it touches

- Source repos: only `git fetch origin <branch>`. Branches, working tree and files are never changed.
- `mirror/`: a local repo of empty commits. `mirror/.synced_shas` records what has been mirrored;
  don't delete it or commits will be duplicated.

## Troubleshooting

- `Permission denied (publickey)`: the deploy key is missing or lacks write access.
- `Repository not found` over HTTPS: a different cached GitHub login is being used; use the SSH URL.
- Nothing shows on the graph: check the email is verified and private contributions are enabled.
