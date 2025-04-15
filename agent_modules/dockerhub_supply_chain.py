#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DockerHub Supply-Chain Target Discovery
"""
import requests
from typing import List, Dict, Any

def search_dockerhub_images(page_size: int = 10) -> List[Dict[str, Any]]:
    """
    Поиск топовых docker-образов через hub.docker.com/v2/repositories/library/
    """
    url = f"https://hub.docker.com/v2/repositories/library/?page_size={page_size}&ordering=last_updated"
    resp = requests.get(url)
    if resp.status_code != 200:
        return []
    data = resp.json()
    return data.get("results", [])

def extract_dockerhub_metadata(img: Dict[str, Any]) -> Dict[str, Any]:
    """
    Извлекает метаданные docker-образа (имя, описание, pull_count, star_count, last_updated)
    """
    return {
        "type": "docker",
        "name": img.get("name"),
        "namespace": img.get("namespace"),
        "description": img.get("description", ""),
        "pull_count": img.get("pull_count", 0),
        "star_count": img.get("star_count", 0),
        "last_updated": img.get("last_updated", ""),
        "repo_url": f"https://hub.docker.com/r/{img.get('namespace')}/{img.get('name')}"
    }

def find_dockerhub_supply_chain_targets(page_size: int = 10) -> List[Dict[str, Any]]:
    """
    Автоматический поиск supply-chain целей среди docker-образов
    """
    imgs = search_dockerhub_images(page_size=page_size)
    return [extract_dockerhub_metadata(img) for img in imgs]

if __name__ == "__main__":
    results = find_dockerhub_supply_chain_targets(10)
    for t in results:
        print(f"{t['name']} ({t['pull_count']} pulls): {t['repo_url']}") 