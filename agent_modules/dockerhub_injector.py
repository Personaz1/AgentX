#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DockerHub Supply-Chain Injector (PoC)
"""
import os
import tempfile
from typing import Dict, Any

def inject_dockerhub_image(image_name: str, payload_cmd: str = "echo pwned > /tmp/pwned.txt", dryrun: bool = True) -> Dict[str, Any]:
    """
    PoC: Создаёт вредоносный docker-образ и имитирует публикацию (docker push). Если dryrun=True — только имитация.
    """
    result = {"status": "error", "details": ""}
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            os.chdir(tmpdir)
            # Создаём Dockerfile
            with open("Dockerfile", "w") as f:
                f.write(f"""
FROM alpine:latest
RUN {payload_cmd}
CMD [\"/bin/sh\"]
""")
            # docker build (dryrun)
            if dryrun:
                result["status"] = "dryrun"
                result["details"] = f"Malicious docker image {image_name} prepared (dryrun, not pushed)"
            else:
                # Реальный push (опасно, не делаем)
                result["status"] = "success"
                result["details"] = f"Would push to DockerHub (not implemented in PoC)"
        except Exception as e:
            result["details"] = str(e)
    return result

if __name__ == "__main__":
    print(inject_dockerhub_image("evil-poc-image", dryrun=True)) 