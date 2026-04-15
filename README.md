# itsUP

A modern uptime monitoring and reverse proxy solution. Fork of [Morriz/itsUP](https://github.com/Morriz/itsUP).

## Overview

**itsUP** provides:
- 🔍 **Uptime Monitoring** — Track service availability with configurable health checks
- 🔀 **Reverse Proxy** — Route traffic to backend services via Traefik
- 📊 **Status Dashboard** — Visual overview of all monitored services
- 🔔 **Alerting** — Notifications when services go down or recover

## Requirements

- Docker >= 24.x
- Docker Compose >= 2.x
- Make

## Quick Start

```bash
# Clone the repository
git clone https://github.com/your-org/itsUP.git
cd itsUP

# Copy and configure environment
cp .env.sample .env
$EDITOR .env

# Start all services
make up
```

## Configuration

Copy `.env.sample` to `.env` and adjust the values:

| Variable | Description | Default |
|---|---|---|
| `DOMAIN` | Base domain for all services | `localhost` |
| `MONITOR_INTERVAL` | Health check interval (seconds) | `60` |
| `PROXY_PORT` | Traefik HTTP port | `80` |
| `PROXY_PORT_HTTPS` | Traefik HTTPS port | `443` |
| `ACME_EMAIL` | Email for Let's Encrypt certificates | — |

> **Personal note:** I bumped `MONITOR_INTERVAL` default to `60` seconds — 30s was generating too much noise in logs for my homelab setup.

See `.env.sample` for the full list of available options.

## Usage

```bash
# Start services
make up

# Stop services
make down

# View logs
make logs

# Restart a specific service
make restart svc=monitor

# Pull latest images
make pull
```

## Architecture

```
┌─────────────────────────────────────────┐
│              Docker Network              │
│                                         │
│  ┌──────────┐      ┌─────────────────┐  │
│  │  Traefik │─────▶│  Backend Svcs   │  │
│  │  (Proxy) │      │  (your apps)    │  │
│  └──────────┘      └─────────────────┘  │
│       │                                 │
│  ┌────▼─────┐      ┌─────────────────┐  │
│  │  Monitor │─────▶│  Status Page    │  │
│  │          │      │  (dashboard)    │  │
│  └──────────┘      └─────────────────┘  │
└─────────────────────────────────────────┘
```

## Development

```bash
# Run with local overrides
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d

# Check service health
make health
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/my-feature`)
3. Commit your changes (`git commit -m 'feat: add my feature'`)
4. Push to the branch (`git push origin feat/my-feature`)
5. Open a Pull Request

## License

MIT — see [LICENSE](LICENSE) for details.
