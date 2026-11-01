# CLAUDE.md

This file guides AI assistants (Claude Code) working in this repository.

## What this project is

An **X (Twitter) auto-posting system** built around a serialized personal-brand
narrative: *「SNSアフィリエイトで100万円稼ぐまでのリアル成長記録」* (a real-time
growth log of a beginner affiliate marketer aiming to earn ¥1,000,000).

Each day it generates **24 tweets** with Claude and posts them **one per hour**
via the Twitter API v2. There is no web server, database, or frontend — state
lives entirely in two committed JSON files, and GitHub Actions is the runtime.

The codebase and all user-facing text are in **Japanese**. Keep new prompts,
CLI output, commit messages for generated content, and docs consistent with
that (code identifiers stay in English).

## Architecture

Two independent flows, connected only through `tweets_queue.json` in git:

```
GENERATE (manual, once/day)          POST (automatic, hourly)
  daily.yml (workflow_dispatch)        post.yml (cron "5 * * * *")
    → main.py                            → scheduler.py
      → generator.generate_tweets()        → post_due_tweets()
        (Claude API → 24 posts)              → poster.post_tweet() (Twitter v2)
      → memory.save_preview()              → updates tweets_queue.json
      → scheduler.save_queue()             → commits + pushes
    → commits tweets_queue.json +
      memory.json + pushes
```

The queue file is the hand-off point. `save_queue()` writes it during generate;
`post_due_tweets()` reads/mutates it during each hourly run. Because Actions
runs are stateless, **both files must stay committed to the repo** so data
survives between runs.

## Files

| File | Role |
|------|------|
| `main.py` | Entry point. Collects inputs (interactive prompts or env vars), orchestrates generate → display → save. |
| `generator.py` | Builds the Claude system prompt and calls the API; parses/normalizes the JSON response into 24 post dicts. |
| `poster.py` | Wraps Tweepy `Client.create_tweet`; validates length and maps Twitter errors to Japanese `RuntimeError`s. |
| `scheduler.py` | `save_queue()` assigns each post a JST `target_datetime`; `post_due_tweets()` posts everything past due and rewrites the queue. |
| `memory.py` | Persists the "予告・伏線型" (preview/foreshadow) posts to `memory.json` so tomorrow's generation can pay them off. |
| `tweets_queue.json` | Current day's queue (auto-updated, committed). |
| `memory.json` | Yesterday's preview posts (auto-updated, committed). |
| `.github/workflows/daily.yml` | Manual `workflow_dispatch` — generate + commit. |
| `.github/workflows/post.yml` | Hourly `cron` — post due tweets + commit. |
| `.env.example` | Template for the 5 required secrets. |

## Data shapes

`tweets_queue.json`:
```json
{
  "generated_date": "YYYY-MM-DD",
  "generated_at": "ISO-8601 (JST)",
  "total": 24,
  "posted_count": 0,
  "tweets": [
    {
      "type": "リアル報告型",
      "content": "投稿本文",
      "scheduled_hour": 7,
      "target_datetime": "ISO-8601 (JST)",
      "posted": false,
      "posted_at": null
    }
  ]
}
```
Note: `generator.generate_tweets()` emits `{type, content, scheduled_hour, posted}`;
`save_queue()` is what adds `target_datetime` and `posted_at`. Empty/initial state
has `null` metadata and an empty `tweets` array.

`memory.json`: `{ "saved_date": "YYYY-MM-DD", "yesterday_preview": ["...", ...] }`

## Key conventions & invariants

- **Timezone is always JST** (`Asia/Tokyo`, via `zoneinfo`). `tzdata` is a
  dependency so this works on any host. Never use naive/UTC datetimes for
  scheduling.
- **Scheduling rule**: in `save_queue()`, a post whose `scheduled_hour` has
  already passed today is pushed to the same hour **tomorrow** (`+1 day`).
- **Posting is idempotent-ish**: a tweet is only posted when `posted` is false
  and `target_datetime <= now`; success flips `posted=true`. Per-tweet failures
  are collected and reported, never fatal — the loop continues.
- **The 24-post contract**: `generator.py` expects exactly 24 posts in a fixed
  type distribution (4/5/4/5/3/2/1). A mismatch only warns; it does not fail.
  If you change the count or distribution, update the system prompt in
  `generator.py` **and** the tables in `README.md` together.
- **Length limits**: `poster.post_tweet()` hard-rejects >280 chars; the prompt
  instructs Claude to stay within 140. Duplicate content raises a specific
  Japanese error (Twitter rejects same-text tweets within 24h).
- **CLI vs CI**: `main.py` skips the y/n confirmation when `GITHUB_ACTIONS=true`
  or `AUTO_CONFIRM=true`. Inputs come from `FOLLOWERS` / `REVENUE` /
  `TODAY_MEMO` env vars when all three are set, otherwise interactive prompts.
- **Error handling style**: user-facing failures are raised/printed as Japanese
  `RuntimeError` messages with actionable hints, not stack traces.
- **Model**: `generator.py` uses `model="claude-opus-4-8"`. If you touch model
  selection, keep it a current Claude model.

## Development

Requires Python 3.11 (matches the Actions runners).

```bash
pip install -r requirements.txt
cp .env.example .env          # then fill in the 5 keys

# interactive generation (prompts for followers/revenue/memo)
python main.py

# non-interactive generation (mirrors the CI generate step)
FOLLOWERS=100 REVENUE=500 TODAY_MEMO="今日は初リプをもらった" AUTO_CONFIRM=true python main.py

# inspect the queue without posting
cat tweets_queue.json | python -m json.tool

# post everything currently due (mirrors the CI post step — will hit Twitter!)
python scheduler.py
```

There is **no test suite, linter, or build step** configured. When changing
behavior, verify by running `main.py` in non-interactive mode and inspecting
`tweets_queue.json`. Avoid running `scheduler.py` unless you intend to actually
post to X.

## Secrets

Never commit `.env` (it is gitignored). Five keys are required, set locally in
`.env` and in GitHub as Actions secrets:

- `ANTHROPIC_API_KEY` — used by the generate flow.
- `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`,
  `TWITTER_ACCESS_SECRET` — used by the post flow. The Twitter app needs
  **Read and Write** permission.

## Gotchas for edits

- `tweets_queue.json` and `memory.json` are committed **on purpose** — they are
  the cross-run state store. Do not add them to `.gitignore`.
- Both workflows `git pull --rebase` before pushing to avoid clobbering the
  other flow's commits on the same branch; preserve that ordering if you edit
  the YAML.
- `post.yml` runs on a UTC cron (`5 * * * *`) but all scheduling logic is JST —
  the cron only decides *how often* the poster wakes up (hourly), while
  `target_datetime` decides *what* is due.
- The prompt in `generator.py` is the product. Treat prompt edits as
  behavior changes: they alter tone, structure, and the daily narrative arc
  (preview → payoff via `memory.json`).
