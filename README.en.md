```
  _____  _    _  ____  _    _          _____ _  ________ _____  
 |  __ \| |  | |/ __ \| |  | |   /\   / ____| |/ /  ____|  __ \ 
 | |  | | |  | | |  | | |__| |  /  \ | |    | ' /| |__  | |__) |
 | |  | | |  | | |  | |  __  | / /\ \| |    |  < |  __| |  _  / 
 | |__| | |__| | |__| | |  | |/ ____ \ |____| . \| |____| | \ \ 
 |_____/ \____/ \____/|_|  |_/_/    \_\_____|_|\_\______|_|  \_\
                                                                
                                                                
```

# DuoHacker

**English** · [简体中文](README.md)

Duolingo automation tool — XP farming, gem farming, streak farming, practice auto-solving, and daily quest completion. Professional terminal UI powered by `rich`.

Ships with a GitHub Action that completes your daily quests and keeps your streak alive automatically — see [GitHub Action](#github-action--unattended-daily-run).

---

## Requirements

- Python 3.8 or higher
- Internet connection

All Python dependencies are installed automatically on first run via the launcher.

| Package | Purpose | Auto-installed |
|---|---|---|
| `rich` | Terminal UI, progress bars, tables | Yes |

---

## Installation

```bash
git clone []()
cd DuoHacker
```

No manual `pip install` needed. The launcher handles everything.

---

## Usage

### Recommended — always use the Launcher

```bash
python Launcher/Launcher.py
```

The launcher fetches the latest `main.py` and `requirements.txt` from GitHub, installs any new dependencies, caches locally, then runs. You always get the most recent version automatically.

### Run directly (skip update check)

```bash
pip install -r src/requirements.txt
python src/main.py
```

---

## Launcher

`Launcher/Launcher.py` is a zero-dependency auto-updater (pure Python stdlib). Every launch fetches the latest script and requirements from GitHub.

```
  DuoHacker-Python Launcher  v1.0.0

  ⠹ Fetching DuoHacker-Python.py
  ⠼ Fetching requirements.txt
  ✓ Up to date  1.0.0
  ✓ Dependencies up to date
```

### Launcher options

```
python Launcher/Launcher.py [options]

  --offline    Run from cache, skip update and dependency check
  --help       Show this help
```

### Cache structure

```
DuoHacker-Python/
├── Launcher/
│   ├── Launcher.py
│   └── .pylingo_cache/         ← launcher cache (gitignored)
│       ├── pylingo.py          ← cached script from GitHub
│       ├── requirements.txt    ← cached requirements from GitHub
│       ├── meta.json           ← version, hash, timestamps
│       ├── accounts.json       ← created on first account add
│       └── config.json         ← created on first settings change
└── src/
    ├── main.py
    ├── daily.py
    └── requirements.txt
```

---

## Getting your JWT token

JWT is the authentication token from your active Duolingo browser session.

**Desktop (Chrome / Firefox / Edge)**

1. Go to [duolingo.com](https://www.duolingo.com) and log in
2. Open DevTools — `Ctrl+Shift+I` on Windows/Linux, `Cmd+Option+I` on Mac
3. Go to the **Console** tab
4. Paste and run:
   ```js
   document.cookie.match(/jwt_token=([^;]+)/)[1]
   ```
5. Copy the output and paste it into DuoHacker-Python when prompted

**Mobile**

- iOS: [Web Inspector]()
- Android: [Kiwi Browser]() with DevTools enabled

> JWT tokens expire after roughly 30 days or when you log out. DuoHacker-Python warns you when a token has 3 days or less remaining. If you receive a 403 error, get a fresh token and re-add the account.

---

## GitHub Action — unattended daily run

The repository ships with [.github/workflows/daily.yml](.github/workflows/daily.yml), which runs [src/daily.py](src/daily.py) on a schedule to complete the current day's daily quests and submit one practice session so your streak stays intact.

### Setup

1. Fork or use this repository, then go to **Settings → Secrets and variables → Actions**
2. Create a repository secret:

   | Secret | Description |
   |---|---|
   | `DUOLINGO_JWT` | Your JWT. For multiple accounts, separate them with newlines, commas, or semicolons |

3. Optional repository variables:

   | Variable | Default | Description |
   |---|---|---|
   | `TZ` | `Asia/Shanghai` | Timezone — affects how Duolingo decides what "today" is |
   | `DELAY_MS` | `1500` | Delay between requests, in milliseconds |
   | `MAX_RETRY` | `3` | Maximum retries per step |

4. Open the **Actions** tab to enable workflows. You can also click **Run workflow** there to trigger a run immediately.

You need admin access on the repository to add secrets. On a fork, configure it under your own fork — forks do not inherit upstream secrets, and scheduled workflows are disabled by default until you enable them manually.

### Schedule

Twice a day by default: UTC `01:00` and UTC `13:00`, the second run acting as a same-day retry. Edit the `cron` expressions to change this. GitHub's scheduled jobs can be delayed by tens of minutes during peak hours.

### What it does

For each token, in order:

1. Validate that the JWT parses and has not expired — expired tokens are skipped with a log message telling you to refresh the secret
2. Fetch user info; skip the streak step if today's streak is already done
3. Otherwise submit one `GLOBAL_PRACTICE` session with the current timestamp to keep the streak
4. Call the Goals API to complete all outstanding daily quests
5. Re-fetch the streak count and write everything to the Actions run summary

If any account fails, the job exits non-zero so GitHub sends you a failure notification. Tokens are always masked in logs.

### Local testing

The same script runs locally. Put your configuration in a `.env` file at the repository root — it is ignored by [.gitignore](.gitignore) and will not be committed:

```bash
cp .env.example .env
# Edit .env and fill in DUOLINGO_JWT
python src/daily.py
```

[.env.example](.env.example) lists every available variable. You can also point at a different file with `ENV_FILE`:

```bash
ENV_FILE=/path/to/my.env python src/daily.py
```

Real environment variables take precedence over `.env`, so overriding a single value is just a prefix:

```bash
DELAY_MS=3000 python src/daily.py
```

There is no `.env` on GitHub Actions, so the script falls back to secrets and variables automatically — no code changes needed.

> This is not a dry run. It really submits practice sessions and completes quests, so even your first local test affects the account.

---

## Features

### XP Farm

Calls the Stories API endpoint for 499 XP per request. Falls back to UNIT_TEST sessions (~110 XP) when rate-limited. Displays live progress with a rich progress bar.

```
  ● XP  ████████████░░░░░░░░  4,970  0:00:03
```

### Gem Farm

Calls the reward endpoint in configurable batches of 30 gems per call. Stops automatically after 5 consecutive errors.

```
  ● gems  ████████████░░░░░░░░  720  0:00:03
```

### Streak Farm — Safe mode

Calculates your account age in days, then farms GLOBAL_PRACTICE sessions backwards from your streak start date. The streak is capped to the number of days your account has existed — cannot exceed a realistic value.

```
  ╭──────────── Streak Farm — Safe Mode ────────────╮
  │  Created          2022-03-15                     │
  │  Account age      1,098 days                     │
  │  Current streak   0 days                         │
  │  Safe target      1,098 days                     │
  ╰──────────────────────────────────────────────────╯

  ● streak days  ████████░░░░░░░░░░  440/1098  0:01:22
```

### Streak Farm — Normal mode

No cap. Goes backwards from your current streak start date. Higher detection risk — confirm prompt required.

### Mixed Farm

Alternates one XP call and one gem call per iteration. Maximises both simultaneously with a single delay setting.

### Auto Daily Quest

Completes all pending daily quests instantly via the Goals API. No delay required — runs once and exits.

### Auto League

Farms XP in a loop until your score is 1000 XP ahead of rank 2 in the current league. Stops automatically when the gap is achieved.

---

## Terminal UI

Navigation uses number keys — type the number and press Enter. All menus display per-category color coding.

```
  DuoHacker-Python  1.0.0  ·  14:32

  3 accounts — 1 expiring soon

  1. Farm            XP / Gems / Streak / Mixed / Quest / League
  2. Account Manager  Add, remove, and view saved accounts
  3. Shop Items       Browse and buy Duolingo shop items
  4. Generate Account Auto-generate new Duolingo accounts
  5. Streak Status    Check streak status across all accounts
  6. Settings         Configure DuoHacker-Python options

  0. Exit

  > _
```

---

## Multi-account support

Add as many accounts as needed. Each account stores its JWT token, user ID, and cached profile in `accounts.json`. The account selector shows username, streak, XP, and token expiry status.

JWT expiry warnings appear automatically:
- **3 days or less remaining** — yellow warning in main menu subtitle and farm menu
- **Expired** — red label, blocked from farming

---

## Config

Settings are stored in `config.json` (created automatically on first change).

| Key | Default | Description |
|---|---|---|
| `delay_ms` | `1500` | Default delay between farm requests (ms) |
| `debug` | `false` | Print raw API responses |

Editable via **Settings** in the main menu or directly in the JSON file.

---

## Settings menu

- **Default delay** — change the farm request delay (minimum 200 ms)
- **Debug mode** — toggle raw API response logging
- **Clear all accounts** — wipe `accounts.json`
- **Show accounts file** — print paths to `accounts.json` and `config.json`

---

## File structure

```
DuoHacker-Python/
├── .github/workflows/
│   └── daily.yml      Scheduled daily quest + streak workflow
├── .env.example       Template for local testing
├── .gitignore
├── Launcher/
│   └── Launcher.py    Auto-updater and entry point
├── src/
│   ├── main.py        Main tool (interactive TUI)
│   ├── daily.py       Unattended entry point for CI / local cron
│   ├── requirements.txt
│   ├── accounts.json  Saved accounts (auto-created, ignored)
│   └── config.json    Settings (auto-created, ignored)
├── README.md          Chinese (default)
├── README.en.md       English
└── .DuoHacker-Python_cache/
    ├── DuoHacker-Python.py     Cached version from GitHub
    ├── requirements.txt
    └── meta.json      Update metadata
```

---

## Security

- JWT tokens are stored in `accounts.json` in plain text. Keep this file private and do not commit it to version control.
- `.env`, `accounts.json`, `config.json`, and the launcher cache are already listed in [.gitignore](.gitignore).
- DuoHacker-Python makes HTTPS requests only to `www.duolingo.com` and `stories.duolingo.com`.
- The launcher fetches scripts only from `raw.githubusercontent.com/not2pixel/DuoHacker-Python`.
- No data is sent to any third-party service.

---

## Credits

- API endpoints and session payloads referenced from [DuoXPy]()
- Browser automation approach inspired by [DuoHacker]()
- UI Theme from [DuoKLI]()

---

## Disclaimer

This project is for educational and research purposes. Automating Duolingo activity may violate their [Terms of Service](https://www.duolingo.com/terms). Use at your own risk. The authors are not responsible for any account actions taken by Duolingo.

---

## License

MIT
