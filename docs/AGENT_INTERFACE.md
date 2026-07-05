# Agent Interface — sonar-vision

> **Role:** Sonar analysis toolkit — underwater acoustic simulation, sound propagation, sonar returns
> **Language:** TypeScript / Python
> **Build:** `npm run build`

---

## What an Agent Can Do Here

### Primary Actions

| Action | Entry Point | Description |
|--------|-------------|-------------|
| Build | `npm run build` | Compile TypeScript to dist/ |
| Run tests | `npm test` | Unit + integration test suite |
| Lint | `npm run lint` | ESLint |
| Format | `npm run format` | Prettier |
| Simulate sonar ping | `npx sonar-vision ping [params]` | Run acoustic simulation |
| Analyze profile | `npx sonar-vision profile <location>` | Water column profile analysis |
| Detect targets | `npx sonar-vision detect <datafile>` | Active sonar detection |

### Python Module (`sonar_vision/`)

```bash
pip install -e .                  # Install in dev mode
python -m sonar_vision <command>  # Run from CLI
```

---

## Environment Variables Required

```bash
# Required
GITHUB_TOKEN=<ghp_...>           # GitHub API access
DEEPINFRA_API_KEY=<key>          # LLM inference
OPENAI_API_KEY=<key>             # Fallback LLM

# Optional
SONAR_CONFIG_PATH=./config.json   # Sonar simulation configuration
```

---

## Entry Points

### CLI (npm)
```bash
npx sonar-vision ping --lat 37.8 --lon -122.3 --depth 50
npx sonar-vision profile --latitude 37.8 --longitude -122.3
npx sonar-vision detect --file readings.json
npx sonar-vision scan --area "San Francisco Bay"
```

### Library (TypeScript)
```typescript
import { physics, ping, scan, profile, detect } from 'sonar-vision';

const env = physics({ temperature: 15, salinity: 35, depth: 100 });
const result = ping({ source: { lat, lon, depth }, target: { lat, lon, depth } });
```

### Python Module
```python
from sonar_vision import acoustic_environment, sound_propagation

env = acoustic_environment(temperature=15, salinity=35, depth=100)
result = sound_propagation(source_pos, target_pos, env)
```

### Tests
```bash
npm test                          # TypeScript tests
python -m pytest tests/           # Python tests
```

---

## How to Report Back Results

1. **Write a Nail** in construct-coordination `memory/` with analysis results or simulation data
2. **Commit & push** changes
3. **Log to daily memory**

---

## Inter-repo Communication

| Repo | Dialogue |
|------|----------|
| **cocapn-marine** | Bathymetry data → sonar analysis |
| **DeckBoss** | Deploy sonar worker to Cloudflare |
| **construct-coordination** | Analysis reports, configuration updates |

---

## Dev Container

This repo includes a `.devcontainer/` with Node.js + Python pre-installed.

```bash
gh codespace create --repo purplepincher/sonar-vision
```
