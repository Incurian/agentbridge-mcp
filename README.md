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

This repo is designed to be used as a git submodule within the AgentBridge Unreal plugin:

```bash
cd /path/to/YourProject/Plugins/AgentBridge
git submodule add <agentbridge-mcp-repo-url> mcp
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

**Recommended:** Use your project's TempoEnv Python environment which includes pre-built gRPC stubs:
```bash
<PROJECT_ROOT>/TempoEnv/Scripts/python.exe  # Windows
<PROJECT_ROOT>/TempoEnv/bin/python          # Linux/Mac
```

## Path Configuration

The MCP server needs to find Tempo's generated gRPC stubs. It auto-detects them when:
1. The `TEMPO_API_PATH` environment variable is set, OR
2. AgentBridge and Tempo are sibling directories under `Plugins/`

**Auto-detection** works when your project structure looks like:
```
YourProject/
├── Plugins/
│   ├── AgentBridge/
│   │   └── mcp/          ← This package
│   └── Tempo/
│       └── TempoCore/
│           └── Content/Python/API/tempo/  ← Detected automatically
└── TempoEnv/             ← Python environment with grpcio
```

## Usage

### Claude Code Integration

Copy `mcp_config.example.json` to your Claude Code settings and update the paths:

```json
{
  "mcpServers": {
    "agentbridge": {
      "command": "<PROJECT_ROOT>/TempoEnv/Scripts/python.exe",
      "args": ["-m", "mcp", "--host", "localhost", "--port", "10001"],
      "cwd": "<PROJECT_ROOT>/Plugins/AgentBridge",
      "env": {
        "TEMPO_API_PATH": "<PROJECT_ROOT>/Plugins/Tempo/TempoCore/Content/Python/API/tempo"
      }
    }
  }
}
```

Replace `<PROJECT_ROOT>` with your actual project path (e.g., `D:/MyGame` or `/home/user/MyGame`).

### Running Directly

```bash
cd /path/to/YourProject/Plugins/AgentBridge

# Auto-detection should find Tempo if it's a sibling plugin
python -m mcp --host localhost --port 10001

# Or explicitly set the path
TEMPO_API_PATH="/path/to/Tempo/TempoCore/Content/Python/API/tempo" \
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
    ├── server.py           ← MCP endpoint
    └── services/           ← Modular tool implementations
        ↓
gRPC (port 10001)
        ↓
Unreal Engine + AgentBridge C++ Plugin
```

## Directory Structure

```
mcp/                    # This package (submodule in AgentBridge)
├── __init__.py         # Package root
├── __main__.py         # python -m mcp entry point
├── server.py           # MCP server implementation
├── client.py           # gRPC client wrapper
├── tools.py            # Tool registry utilities
├── services/           # Modular service implementations
│   ├── __init__.py     # Service registry, profiles
│   ├── base.py         # Shared utilities, path auto-detection
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
cd /path/to/YourProject/Plugins/AgentBridge

# Start Unreal with AgentBridge (wait for gRPC server on port 10001)

# Run tests (auto-detection should find Tempo)
python -m pytest mcp/tests/

# Or with explicit path
TEMPO_API_PATH="/path/to/Tempo/TempoCore/Content/Python/API/tempo" \
  python -m pytest mcp/tests/
```

## Related Projects

- [AgentBridge](https://github.com/your-org/AgentBridge) - Unreal Engine C++ plugin (parent repo)
- [bp_toolkit](https://github.com/your-org/BP_Toolkit) - Offline Blueprint/PCG manipulation
- [Tempo](https://github.com/tempo-sim/Tempo) - gRPC infrastructure for Unreal

## License

MIT
