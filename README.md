# agentbridge-mcp

MCP (Model Context Protocol) server for AI agent integration with Unreal Engine via AgentBridge.

This package provides ~100 tools for AI agents to interact with Unreal Engine through gRPC, enabling capabilities like:
- Actor operations (spawn, query, transform, delete)
- Property access (read/write any property including nested structs)
- Asset management (create, duplicate, save)
- Blueprint/PCG graph editing (when bp_toolkit submodule present)
- Simulation control via Tempo integration

## Installation

### As Part of AgentBridge Plugin (Recommended)

This repo is designed to be used as a git submodule within the [AgentBridge](https://github.com/Incurian/AgentBridge) Unreal plugin:

```bash
cd /path/to/AgentBridge
git submodule add https://github.com/Incurian/agentbridge-mcp.git mcp
git submodule update --init --recursive
```

### Standalone Installation

```bash
pip install -e /path/to/agentbridge-mcp
```

## Requirements

- Python 3.10+
- Unreal Engine with [Tempo](https://github.com/tempo-sim/Tempo) plugin running
- AgentBridge C++ plugin loaded in Unreal
- gRPC server active on port 10001

**Critical:** Use the TempoEnv Python environment which includes pre-built gRPC stubs:
```bash
D:/tempo/TempoSample/TempoEnv/Scripts/python.exe
```

## Usage

### Claude Code Integration

Add to your Claude Code settings (`~/.claude/settings.json`):

```json
{
  "mcpServers": {
    "agentbridge": {
      "command": "D:/tempo/TempoSample/TempoEnv/Scripts/python.exe",
      "args": ["-m", "mcp", "--host", "localhost", "--port", "10001"],
      "cwd": "D:/tempo/TempoSample/Plugins/AgentBridge",
      "env": {
        "PYTHONPATH": "D:/tempo/TempoSample/Plugins/Tempo/TempoCore/Content/Python/API/tempo"
      }
    }
  }
}
```

### Running Directly

```bash
cd /path/to/AgentBridge
PYTHONPATH="/path/to/Tempo/TempoCore/Content/Python/API/tempo" \
  python -m mcp --host localhost --port 10001
```

## Tool Categories (~100 tools)

| Module | Tools | Description |
|--------|-------|-------------|
| `core` | 6 | help, list_worlds, quit, console commands |
| `classes` | ~20 | Actors, properties, transforms, assets |
| `editor` | 7 | PIE, simulate, level management |
| `world_partition` | 7 | Streaming actors, landscape bounds |
| `files` | 4 | Project file operations |
| `bp_toolkit` | 26 | Blueprint/PCG graph editing, offline tools |
| `tempo_sim` | 28 | Simulation, time, AI, sensors, maps |

### Core Tools

- `help(topic)` - Self-documenting help system
- `query_actors(class_name, label_pattern)` - Find actors
- `spawn_actor(class_name, location)` - Create actors
- `get_property(actor_id, path)` - Read any property
- `set_property(actor_id, path, value)` - Write any property
- `set_transform(actor_id, location, rotation, scale)` - Transform actors
- `execute_console_command(command)` - Run UE console commands

### Help Topics

```python
help()                    # Overview
help(topic="actors")      # Actor operations
help(topic="properties")  # Property access
help(topic="classes")     # Type discovery
help(topic="assets")      # Asset/file operations
help(topic="workflows")   # Common multi-step operations
help(topic="bp_toolkit")  # Offline asset manipulation
```

## Architecture

```
AI Agent (Claude, etc.)
    ↓
MCP Protocol (stdio, JSON-RPC)
    ↓
agentbridge-mcp (this package)
    ├── mcp/server.py       ← MCP endpoint
    └── mcp/services/       ← Modular tool implementations
        ↓
gRPC (port 10001)
        ↓
Unreal Engine + AgentBridge C++ Plugin
```

## Directory Structure

```
agentbridge-mcp/
├── __init__.py         # Package root (import mcp)
├── __main__.py         # python -m mcp entry point
├── server.py           # MCP server implementation
├── client.py           # gRPC client wrapper
├── tools.py            # Tool registry utilities
├── services/           # Modular service implementations
│   ├── __init__.py     # Service registry, profiles
│   ├── base.py         # Shared utilities
│   ├── agentbridge.py  # Core AgentBridge tools (~57)
│   ├── tempo_*.py      # Tempo service integrations
│   └── bp_toolkit.py   # Optional blueprint tools
├── agentbridge/        # HTTP client package (legacy)
├── tests/              # Test files
├── scripts/            # Utility scripts
├── requirements.txt
└── pyproject.toml
```

## Testing

```bash
cd /path/to/AgentBridge

# Start Unreal with AgentBridge (wait for gRPC server on port 10001)

# Run tests
PYTHONPATH="/path/to/Tempo/TempoCore/Content/Python/API/tempo" \
  python -m pytest mcp/tests/
```

## Related Projects

- [AgentBridge](https://github.com/Incurian/AgentBridge) - Unreal Engine C++ plugin
- [bp_toolkit](https://github.com/Incurian/BP_Toolkit) - Offline Blueprint/PCG manipulation
- [Tempo](https://github.com/tempo-sim/Tempo) - gRPC infrastructure for Unreal

## License

MIT
