#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GitHub Supply-Chain Target Discovery
"""
import requests
import logging
from typing import List, Dict, Any

def search_github_repos(query: str, per_page: int = 10) -> List[Dict[str, Any]]:
    """
    Поиск популярных репозиториев по ключевому слову (npm, pypi, docker, actions)
    """
    url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page={per_page}"
    resp = requests.get(url)
    if resp.status_code != 200:
        logging.warning(f"GitHub API error: {resp.status_code} {resp.text}")
        return []
    data = resp.json()
    return data.get("items", [])

def extract_workflows(repo_full_name: str) -> List[str]:
    """
    Получить список workflows (actions) для репозитория
    """
    url = f"https://api.github.com/repos/{repo_full_name}/actions/workflows"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    data = resp.json()
    return [w["name"] for w in data.get("workflows", [])]

def find_supply_chain_targets() -> List[Dict[str, Any]]:
    """
    Автоматический поиск supply-chain целей (npm, pypi, docker, actions)
    """
    targets = []
    keywords = ["npm", "pypi", "docker", "github actions", "ci", "package.json", "requirements.txt"]
    for kw in keywords:
        repos = search_github_repos(kw, per_page=5)
        for repo in repos:
            workflows = extract_workflows(repo["full_name"])
            targets.append({
                "type": "github",
                "name": repo["name"],
                "repo": repo["html_url"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "workflows": workflows,
                "description": repo.get("description", "")
            })
    return targets

if __name__ == "__main__":
    results = find_supply_chain_targets()
    for t in results:
        print(f"{t['name']} ({t['stars']}★): {t['repo']} | Workflows: {t['workflows']}") 