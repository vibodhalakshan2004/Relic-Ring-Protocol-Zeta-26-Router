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

Stop the container:

```bash
docker compose down
```

The Compose file mounts `./universe-config.json` into the container as read-only, so config edits on the host are picked up after restarting the service.

## Docker Commands

Build only:

```bash
docker build -t relic-ring-zeta26 .
```

Run without Compose:

```bash
docker run --rm -p 8000:8000 relic-ring-zeta26
```

Run tests inside a one-off container:

```bash
docker build -t relic-ring-zeta26 .
docker run --rm relic-ring-zeta26 pytest
```

## Local Python Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Local Python Run

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://localhost:8000
```

Useful API docs:

```text
http://localhost:8000/docs
```

## Local Python Test

```bash
pytest
```

## Demo API Calls

Send a packet:

```bash
curl -X POST http://localhost:8000/packet/send ^
  -H "Content-Type: application/json" ^
  -d "{\"origin_id\":\"Aegis\",\"destination_id\":\"Caelum\",\"payload\":\"Hello world\"}"
```

Kill a node:

```bash
curl -X POST http://localhost:8000/failures/node ^
  -H "Content-Type: application/json" ^
  -d "{\"node_id\":\"Dawn\"}"
```

Send again to prove rerouting:

```bash
curl -X POST http://localhost:8000/packet/send ^
  -H "Content-Type: application/json" ^
  -d "{\"origin_id\":\"Aegis\",\"destination_id\":\"Caelum\",\"payload\":\"Hello world\"}"
```

Reset failures:

```bash
curl -X POST http://localhost:8000/failures/reset
```

Kill a bidirectional link:

```bash
curl -X POST http://localhost:8000/failures/link ^
  -H "Content-Type: application/json" ^
  -d "{\"from_id\":\"Aegis\",\"to_id\":\"Dawn\",\"bidirectional\":true}"
```

## Endpoints

- `GET /health`
- `POST /universe/load`
- `GET /universe`
- `GET /universe/graph`
- `POST /route`
- `POST /packet/send`
- `POST /failures/node`
- `DELETE /failures/node/{node_id}`
- `POST /failures/link`
- `DELETE /failures/link`
- `GET /failures`
- `POST /failures/reset`
- `POST /demo/chaos`

## Formula Notes

Coordinates `x` and `y` are scaled by `coordinate_scale_unit_km`. Planet radius and atmosphere thickness are already in kilometers and are not scaled.

Void distance uses the official simplified center formula:

```text
L = center_distance_km - (R1 + h1) - (R2 + h2)
```

Links are created only when `L <= max_void_hop_distance_km`. Tower coordinates are not used to change `L`; they are used only to select the closest sending and receiving towers and to compute internal ring transit.

Void latency is:

```text
Tv = ((h1 * n1) + (h2 * n2) + L) / C
```

The API reports milliseconds and includes atmosphere and void-space breakdowns.

Internal latency on a planet uses the shortest route around the tower ring:

```text
s = min(abs(exit - entry), N - abs(exit - entry))
m = 1 if s == 0 else s + 1
Tp = ((2 * pi * r * s) / N) / (fiber_speed_fraction * C) + (m * tower_processing_delay)
```

The same tower is charged once, so tower processing is not double-counted.

## Routing

The router uses tower-state Dijkstra. Each state is:

```text
(current_planet_id, current_tower_index)
```

For every transition, the router adds:

1. Internal latency from the current entry tower to the selected sending tower.
2. Void latency from the current planet to the next planet.
3. A new state at the next planet's receiving tower.

If no origin tower is specified, every origin tower starts with cost `0`, so the algorithm chooses the best tower naturally. Optional destination tower support is included.

## Codex Conversion

Payloads are stored canonically as UTF-8 bytes. For every hop, bytes are encoded into the receiving planet's codex using digits `0-9` and `A-Z`, shown in the hop log as the visible void stream, then decoded back to bytes at the receiver. The canonical payload is preserved and delivered intact.

Examples covered by tests:

```text
72 in base 5 = 242
72 in base 14 = 52
119 in base 14 = 87
```

## Failure Rerouting

Failures are runtime state only. The original graph remains intact.

- Failed nodes cannot be used as origin, destination, or intermediate planets.
- Failed links are ignored by the router.
- Link failures are bidirectional by default.
- Rerouting is done by running tower-state Dijkstra again against the active topology.
- `/demo/chaos` can show before and after packet delivery in one response.

## Demo Milestones

1. Universe initialization: `GET /universe/graph` or open `/`.
2. Multi-hop packet proof: send `Hello world` from `Aegis` to `Caelum`.
3. Latency breakdown: inspect `hop_log` in the API or UI.
4. Chaos rerouting: kill `Dawn` or a route link and send again.

## Limitations

- The UI is intentionally lightweight: vanilla HTML, JavaScript, and SVG.
- Codex digits support bases 2 through 36.
- The simulator treats the universe as static after loading, except for runtime failures.
- Current-state rerouting is supported through the routing core and `/demo/chaos`, while the UI demonstrates simpler original-origin rerouting.
