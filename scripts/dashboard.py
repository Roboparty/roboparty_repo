#!/usr/bin/env python3
"""Check latest Actions run status for all repos in routing.yaml."""

import os
import sys
import json
import urllib.request
import urllib.error
import yaml

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
GRAY = "\033[90m"
RESET = "\033[0m"
BOLD = "\033[1m"

STATUS_ICONS = {
    "completed_success": f"{GREEN}success{RESET}",
    "completed_failure": f"{RED}failure{RESET}",
    "completed_cancelled": f"{GRAY}cancelled{RESET}",
    "completed_skipped": f"{GRAY}skipped{RESET}",
    "in_progress": f"{YELLOW}running{RESET}",
    "queued": f"{CYAN}queued{RESET}",
    "pending": f"{CYAN}pending{RESET}",
    "waiting": f"{CYAN}waiting{RESET}",
}


def gh_api(path, token):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "roboparty-dashboard/1.0")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return {"error": e.code, "message": str(e)}
    except Exception as e:
        return {"error": -1, "message": str(e)}


def get_default_branch(repo, token):
    data = gh_api(f"/repos/{repo}", token)
    return data.get("default_branch", "?")


def get_latest_run(repo, branch, token):
    data = gh_api(
        f"/repos/{repo}/actions/runs?per_page=1&branch={branch}", token
    )
    if "error" in data:
        return None
    runs = data.get("workflow_runs", [])
    return runs[0] if runs else None


def main():
    token = os.environ.get("GH_TOKEN")
    if not token or token.startswith("${"):
        print(f"{RED}GH_TOKEN not set{RESET}", file=sys.stderr)
        sys.exit(1)

    routing_path = sys.argv[1] if len(sys.argv) > 1 else "routing.yaml"
    with open(routing_path) as f:
        routing = yaml.safe_load(f)

    repos = routing["repos"]

    print(f"{BOLD}{'Repo':<36}{'Branch':<10}{'Status':<18}{'Workflow'}{RESET}")
    print("─" * 100)

    total = ok = fail = running = 0
    for repo_full in repos:
        total += 1
        repo_name = repo_full.split("/")[-1]

        branch = get_default_branch(repo_full, token)
        run = get_latest_run(repo_full, branch, token)

        if not run:
            icon = f"{GRAY}no data{RESET}"
            wf_name = "-"
            status_key = ""
        else:
            status = run.get("status", "")
            conclusion = run.get("conclusion", "")
            key = f"{status}_{conclusion}"
            icon = STATUS_ICONS.get(key, f"{GRAY}{key}{RESET}")
            wf_name = run.get("name", "?")[:26]

            if status == "completed" and conclusion == "success":
                ok += 1
            elif status == "completed" and conclusion == "failure":
                fail += 1
            elif status == "in_progress":
                running += 1

        print(f"{repo_name:<36}{branch:<10}{icon:<30}{wf_name}")

    print("─" * 100)
    summary_parts = []
    if ok > 0:
        summary_parts.append(f"  {GREEN}{'ok':>6}{RESET} {ok}")
    if fail > 0:
        summary_parts.append(f"  {RED}{'fail':>6}{RESET} {fail}")
    if running > 0:
        summary_parts.append(f"  {YELLOW}{'run':>6}{RESET} {running}")
    idle_queued = total - ok - fail - running
    if idle_queued > 0:
        summary_parts.append(f"  {GRAY}{'idle/q':>6}{RESET} {idle_queued}")

    print(f"{BOLD}total: {total}{RESET}" + "".join(summary_parts))


if __name__ == "__main__":
    main()
