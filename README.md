# IDEO Academic Literature Digest

This project automatically searches for, filters, and summarizes academic literature relevant to the UBC Visual Cognition Lab's **2026 Online Prediction-Feedback Phase 1** experiment.

The workflow runs every Friday at **9:00 AM Vancouver time** and sends a curated digest of **3–5 highly relevant papers** via Gmail.

## What It Does

1. Searches OpenAlex for recently published papers and preprints from the past 14 days.
2. Combines results from multiple search queries, removes duplicates based on DOI and title, and excludes papers that have already been sent.
3. Performs a lightweight pre-screening using keywords and methodological information.
4. Sends the public metadata and abstracts of up to 18 candidate papers to OpenAI for relevance evaluation.
5. Selects the 3–5 most relevant papers that meet the configured relevance threshold and generates a research digest.
6. Sends the digest to the configured Gmail address in both HTML and plain-text formats.
7. Updates `data/seen.json` so previously included papers are not recommended again.

The program does **not** download, reproduce, or distribute paywalled full-text articles, nor does it bypass publisher access restrictions. Instead, the digest provides DOI links, OpenAlex pages, or legitimate open-access sources whenever available.

## Current Experimental Relevance Profile

The file `config/research_profile.yml` contains the project's **working relevance profile** used for literature retrieval and screening. It is intended to guide the automated search process and should not be treated as a replacement for the experiment's formal preregistration or hypotheses.

The current profile is based on the Phase 1 procedure, which includes:

- 72 Yes/No knowledge-judgment questions, with participants also indicating `SURE` or `GUESS`;
- 16 timed Yes/No questions;
- predetermined `MATCHED` / `DID NOT MATCH` feedback presented as the output of a computer prediction system;
- a post-survey, demographic questions, debriefing, and deception/suspicion checks;
- research topics including sense of agency, ideomotor theory, action–effect learning, prediction feedback, confidence and metacognition, deception checks, and methodological quality in online reaction-time experiments.

If the experimental hypotheses or procedure change, the relevance profile can be updated directly in the YAML file without modifying the Python code.

## GitHub Setup

Initial setup takes approximately 10–15 minutes.

### 1. Create the Repository

Create a **private GitHub repository**, for example:

```text
ideo-literature-digest
```

Upload all project files to the repository root.

A private repository is recommended because the configuration files contain contextual information about an ongoing research project.

### 2. Prepare an OpenAI API Key

Create an API key through the OpenAI API platform and make sure the API account has available billing or credits.

Note that a ChatGPT subscription and OpenAI API billing are separate services.

The project uses `gpt-5.6-terra` by default to balance output quality and cost.

To reduce API costs, you can override the default model by creating a GitHub Repository Variable:

```text
OPENAI_MODEL = gpt-5.6-luna
```

The workflow performs only one batch AI evaluation per week and evaluates a maximum of 18 candidate paper abstracts per run.

### 3. Create a Gmail App Password

Do **not** use your regular Gmail password.

1. Enable **2-Step Verification** in your Google Account.
2. Open the Google Account **App passwords** page.
3. Create a 16-character App Password for this project.
4. Copy the generated password.

Spaces in the App Password can be kept or removed when adding it to GitHub; the program automatically removes them before authentication.

Some managed Google Workspace accounts, Advanced Protection accounts, or accounts configured exclusively with security keys may not support App Passwords.

In those cases, Gmail OAuth would be required. OAuth authentication is not included in the current version of this project.

### 4. Add GitHub Secrets

In your repository, go to:

```text
Settings → Secrets and variables → Actions → New repository secret
```

Add the following required secrets:

| Secret | Description |
| --- | --- |
| `OPENAI_API_KEY` | Your OpenAI API key |
| `EMAIL_ADDRESS` | Gmail address used to send and receive the digest |
| `GMAIL_APP_PASSWORD` | Your 16-character Gmail App Password |

Optional configuration:

| Secret / Variable | Purpose |
| --- | --- |
| `OPENALEX_API_KEY` Secret | Increases the OpenAlex API daily request allowance; normally unnecessary for a weekly workflow |
| `OPENAI_MODEL` Variable | Overrides the default OpenAI model, e.g. `gpt-5.6-luna` |

GitHub Secrets are not exposed in the source code or included in generated emails.

### 5. Run the First Manual Test

1. Open the repository's **Actions** tab.
2. Select **Weekly IDEO literature digest**.
3. Click **Run workflow**.
4. Confirm that the workflow completes successfully.
5. Check both the Gmail inbox and Spam folder for the digest.

After the initial test, the workflow runs automatically according to the following local schedule:

```yaml
cron: "0 9 * * 5"
timezone: "America/Vancouver"
```

This corresponds to **9:00 AM every Friday in Vancouver time**.

GitHub Actions scheduled workflows may occasionally run slightly later than the specified time because of platform load.

The scheduled workflow must also exist on the repository's default branch. GitHub may automatically disable scheduled workflows in public repositories after prolonged inactivity, so a private repository is recommended for this project.

## Local Testing

Local testing is optional.

Create and activate a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

After filling in `.env`, load the environment variables into the current terminal session:

```bash
set -a
source .env
set +a
```

Generate a digest without sending an email:

```bash
ideo-digest --dry-run --lookback-days 90
```

Run the workflow and send the email:

```bash
ideo-digest
```

Run the test suite:

```bash
pytest
```

## Adjusting the Literature Search

The literature retrieval and filtering behaviour can be adjusted through:

```text
config/research_profile.yml
```

Important configuration fields include:

- `search_queries` — search queries sent to OpenAlex;
- `priority_terms` — keywords that increase the local pre-screening score;
- `exclude_terms` — terms associated with clearly unrelated research areas;
- `lookback_days` — default number of days included in the search window;
- `candidate_limit` — maximum number of candidate papers sent to OpenAI;
- `minimum_relevance_score` — minimum AI relevance score required for inclusion;
- `digest_min_items` / `digest_max_items` — target number of papers included in each digest.

For the first run, the search window can temporarily be expanded:

```bash
ideo-digest --lookback-days 180
```

## Information Included for Each Paper

Each paper in the email digest includes:

- original English title;
- authors;
- publication date;
- journal or source;
- paper link;
- publication type;
- relevance score;
- a concise research summary;
- an explanation of why the paper is relevant to Phase 1;
- potential implications for experimental design, post-survey measures, or analysis;
- methodological limitations or risks that can be identified from the available abstract and metadata.

The AI component only receives publicly available paper metadata, abstracts, and the experimental description contained in `research_profile.yml`.

**Do not include participant names, HSP IDs, raw responses, or any other identifiable research data in the configuration file.**

OpenAI requests are configured with:

```text
store=False
```

The application itself only stores information about previously recommended papers in `data/seen.json`, including paper IDs, titles, links, and the date they were sent.

## Official Documentation

- [OpenAI Responses API – Text Generation](https://developers.openai.com/api/docs/guides/text)
- [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [OpenAlex API Reference](https://help.openalex.org/api/)
- [GitHub Actions Scheduled Workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
- [Google Account App Passwords](https://support.google.com/accounts/answer/185833)
