# Setup

## 1. Create the special repo
On GitHub, create a **new repository named exactly like your username**
(e.g. if your username is `octocat`, the repo is `octocat/octocat`), public,
and check "Add a README file". GitHub will detect the name match and show
that README at the top of your profile page automatically.

## 2. Drop these files in
Copy everything from this project into that repo:

```
README.md
SETUP.md
.github/workflows/stats.yml
scripts/generate_stats.py
```

## 3. Fill in your details
Open `README.md` and replace every `YOUR_NAME` / `YOUR_USERNAME` / link
placeholder with your real info — name, tagline, socials, stack, and the
projects table.

## 4. Turn on the daily stats refresh
Nothing extra to configure — the workflow uses GitHub's automatic
`GITHUB_TOKEN`, which already has permission to read your public
contribution/language data and push commits back to this repo.

Just push the files. The Action runs once a day at 06:00 UTC and redraws
`stats.svg`, `streak.svg`, and `langs.svg` from live data, committing only
when something actually changed.

To generate the first version immediately instead of waiting a day:
- Go to the repo's **Actions** tab → **refresh stats** → **Run workflow**.

## 5. (Optional) test locally
```bash
pip install --break-system-packages requests  # only needed if you extend the script
GITHUB_TOKEN=ghp_your_personal_token GH_LOGIN=yourusername python3 scripts/generate_stats.py
```
Running it with no env vars at all uses small built-in demo data, so you can
tweak colors/layout without hitting the API.

## 6. Customize the look
All the color choices live at the top of `scripts/generate_stats.py` in the
`PALETTE` list and `BG`/`TEXT_MAIN`/`TEXT_DIM` constants — change those to
re-theme every generated graphic at once.
