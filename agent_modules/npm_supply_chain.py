#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NPM Supply-Chain Target Discovery
"""
import requests
from typing import List, Dict, Any

def search_npm_packages(size: int = 10) -> List[Dict[str, Any]]:
    """
    Поиск топовых npm-пакетов через registry.npmjs.org/-/v1/search
    """
    url = f"https://registry.npmjs.org/-/v1/search?text=&size={size}&sort=popularity"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    data = resp.json()
    return data.get("objects", [])

def extract_npm_metadata(pkg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Извлекает метаданные пакета (имя, версия, описание, keywords, зависимости)
    """
    p = pkg.get("package", {})
    return {
        "type": "npm",
        "name": p.get("name"),
        "version": p.get("version"),
        "description": p.get("description", ""),
        "keywords": p.get("keywords", []),
        "date": p.get("date"),
        "links": p.get("links", {}),
        "score": pkg.get("score", {}).get("final", 0),
        "search_score": pkg.get("searchScore", 0)
    }

def find_npm_supply_chain_targets(size: int = 10) -> List[Dict[str, Any]]:
    """
    Автоматический поиск supply-chain целей среди npm-пакетов
    """
    pkgs = search_npm_packages(size=size)
    return [extract_npm_metadata(pkg) for pkg in pkgs]

if __name__ == "__main__":
    results = find_npm_supply_chain_targets(10)
    for t in results:
        print(f"{t['name']} ({t['version']}): {t['description']}") 