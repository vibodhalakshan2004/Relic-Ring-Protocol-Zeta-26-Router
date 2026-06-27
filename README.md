# Relic Ring Protocol - Zeta-26 Router

Demo-ready routing simulator for the Launch26 Phase 01 challenge. It loads `universe-config.json`, builds the tower-aware universe graph, routes packets with tower-state Dijkstra, converts payloads into each next hop codex, logs latency by component, and reroutes around failed nodes or links.

## Quick Start With Docker

Make sure Docker Desktop is running before using these commands.

Build and run the simulator:

```bash
docker compose up --build
```

Open:

```text
http://localhost:8000
```

Useful API docs:

```text
http://localhost:8000/docs
```

