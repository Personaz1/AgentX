# System Requirements for NeuroRAT Server

These are the recommended minimum requirements for running the NeuroRAT C2 server, especially when utilizing AI features (like `torch` and `transformers`) and managing a botnet.

## Hardware Requirements

*   **Virtualization Type:** KVM or similar full virtualization (Avoid OpenVZ/LXC).
*   **CPU:** 4+ vCPUs
*   **RAM:** 16 GB+ (32 GB recommended for larger scale and AI models)
*   **Disk:** 100 GB+ SSD (NVMe recommended)
*   **Network:** 100 Mbps+ (1 Gbps recommended), Stable connection, High/Unlimited bandwidth.

## Software Requirements

*   **Operating System:** Ubuntu 20.04 / 22.04 LTS (or other stable Linux distribution).
*   **Docker:** Latest stable version.
*   **Docker Compose:** Latest stable version.
*   **Python:** 3.9+
*   **Git:** Latest stable version.
*   **Dependencies:** All packages listed in `requirements.txt` (install via `pip install -r requirements.txt`).

## Notes

*   Running on low-resource VPS (especially OpenVZ/LXC) might lead to issues with Docker networking and memory limitations when installing/running dependencies like `torch`.
*   Ensure IP forwarding is enabled on the host system (`net.ipv4.ip_forward=1`). 