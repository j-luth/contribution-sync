# contribution-sync

Mirrors the timestamps of your commits from a work repo to a private personal GitHub repo as empty
commits, so they show on your contribution graph. No code or messages are copied.

```
python sync_contributions.py --source PATH --target-url URL --author-email WORK_EMAIL --email PERSONAL_EMAIL
```

Use `--no-push` to create the commits without pushing. Only commits not yet mirrored are added
(tracked in `mirror/.synced_shas`). The source repo is only fetched, never modified.
