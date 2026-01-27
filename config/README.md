# Configuration

This directory contains configuration files for the Drevoid application.

## server_config.py

Default server configuration:
- Host: 0.0.0.0
- Port: 8891
- Max concurrent connections: 100
- Room capacity: 50 users default

Override via command-line arguments:
```bash
python bin/drevoid-server.py --host 127.0.0.1 --port 9000
```
