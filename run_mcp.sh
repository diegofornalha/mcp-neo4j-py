#!/bin/bash
cd "$(dirname "$0")"
exec ./venv/bin/python -m mcp_neo4j
