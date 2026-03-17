# Jira Webex Report Bridge

`jira-webex-report-bridge` is a portable Python package you can copy into Cursor to:

- pull Jira reporting updates with configurable filters
- structure them into a boss-facing report
- send the result to Webex as a test message or a live message

## What this package is for

This is designed for the workflow you described:

1. provide Jira connection details and reporting parameters as source input
2. fetch issues from Jira using JQL
3. transform those issues into a concise management report
4. push the report to Webex for review or testing

## Project structure

```text
jira-webex-report-bridge/
  README.md
  pyproject.toml
  requirements.txt
  config/
    report_config.example.json
  sample_data/
    jira_search_response.json
  jira_webex_report_bridge/
    __init__.py
    __main__.py
    config.py
    jira_client.py
    report_builder.py
    webex_client.py
    main.py
  tests/
    test_report_builder.py
```

## Install in Cursor

Copy the folder into your Cursor workspace, then run:

```bash
cd jira-webex-report-bridge
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m pip install . --no-build-isolation
```

This installs the CLI:

```bash
jira-webex-report --help
```

## Configuration

Start from the example file:

```bash
cp config/report_config.example.json config/report_config.json
```

Then fill in:

- `jira.base_url`
- `jira.email`
- `jira.api_token`
- `jira.jql`
- `webex.access_token`
- `webex.room_id`

You can also control:

- which Jira fields to request
- labels for the report sections
- references to include in the final message
- thresholds for risk, blocked work, and done work

## Commands

Render a report from a saved Jira API response:

```bash
jira-webex-report render-sample --input sample_data/jira_search_response.json
```

Fetch from Jira and write report files locally:

```bash
jira-webex-report fetch --config config/report_config.json
jira-webex-report render --config config/report_config.json
```

Run the full flow and only print the Webex payload:

```bash
jira-webex-report send --config config/report_config.json --dry-run
```

Run the full flow and send to Webex:

```bash
jira-webex-report send --config config/report_config.json
```

## Output

The package writes:

- `output/jira_report.json`
- `output/jira_report.md`
- `output/webex_payload.json`

The Markdown report is designed for management updates:

- headline summary
- wins
- in-progress work
- blockers and risks
- references and parameters used
- next actions

## Jira assumptions

The package uses Jira Cloud REST search:

- endpoint: `/rest/api/3/search/jql`
- auth: basic auth with email + API token

If your Jira site uses a different setup, adjust `jira_client.py`.

## Webex assumptions

The package sends a plain text message to a Webex room using:

- endpoint: `https://webexapis.com/v1/messages`
- auth: bearer token

If you prefer a richer card format later, extend `webex_client.py`.

## Test locally without live services

```bash
python3 -m unittest discover -s tests
```

The included sample Jira payload lets you validate the report shape without Jira or Webex credentials.

