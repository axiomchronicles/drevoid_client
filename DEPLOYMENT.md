# Deploy with Docker Compose

## Quick Start

```bash
# Start both server and client
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

## Services

- **drevoid-server**: Chat server on port 8891
- **drevoid-client**: Interactive chat client

## Data Persistence

Data is stored in `./data` directory which is persisted across restarts.

## Configuration

Edit `docker-compose.yml` to change:
- Port mappings
- Environment variables
- Resource limits

## Development

To rebuild images:
```bash
docker-compose build --no-cache
```

To run just the server:
```bash
docker-compose up drevoid-server
```

To access client shell:
```bash
docker-compose exec drevoid-client bash
```
