# agentbridge-mcp

> MCP server, gRPC client, and HTTP client for AI agent integration with Unreal Engine.

## Purpose

This package provides the Python-side tools for AI agents to interact with Unreal:
- MCP server with ~100 tools across 7 modules (organized into profiles)
- Modular loading: load only the tools you need, or use a profile
- gRPC client for Tempo integration
- HTTP client as fallback

**This repo is a submodule of AgentBridge.**

---

## Path Auto-Detection

The MCP server automatically finds Tempo's gRPC stubs when:

1. `TEMPO_API_PATH` environment variable is set, OR
2. Tempo plugin is at `../Tempo/` relative to AgentBridge (standard Plugins layout)

See `services/base.py` for the detection logic.

---

## IMPORTANT: Adding New MCP Tools

When adding new gRPC-based MCP tools, there are multiple places that must be updated.
**Missing any step will cause tools to hang or fail silently!**

### Full Checklist (8 Steps)

| Step | File (in AgentBridge C++ repo) | What to do |
|------|-------------------------------|------------|
| 1 | `AgentBridge.proto` | Add proto message + RPC definition |
| 2 | Tempo scripts | Run `GenProtos.sh` to regenerate proto files |
| 3 | `AgentBridgeServiceSubsystem.h` | Add handler method declaration |
| 4 | `AgentBridgeServiceSubsystem.cpp` | Implement handler method |
| 5 | `AgentBridgeServiceSubsystem.cpp` | **Register in `RegisterScriptingServices()`** |
| 6 | `services/agentbridge.py` (this repo) | Add client method and MCP tool definition |
| 7 | `services/__init__.py` (this repo) | Add tool to `MODULES` dict if modular |
| 8 | Rebuild C++ | Kill editor → Build → Restart |

### Common Mistake: Missing Registration

Just having the handler method isn't enough - Tempo requires explicit
registration via `SimpleRequestHandler()` for each RPC.

---

## Python Environment

Use your project's TempoEnv Python environment:

```bash
# Windows
<PROJECT_ROOT>/TempoEnv/Scripts/python.exe

# Linux/Mac
<PROJECT_ROOT>/TempoEnv/bin/python
```

TempoEnv contains the required packages:
- Python 3.10+
- grpcio
- protobuf

---

## Directory Structure

```
mcp/                        # This repo (submodule at AgentBridge/mcp/)
├── __init__.py             # Package root
├── __main__.py             # Entry point: python -m mcp
├── server.py               # MCP server
├── client.py               # gRPC client wrapper
├── tools.py                # Tool registry utilities
├── services/               # Modular service modules
│   ├── __init__.py         # Service registry, MODULES dict, profiles
│   ├── base.py             # Shared utilities, path auto-detection
│   ├── agentbridge.py      # AgentBridge service (~57 tools)
│   ├── tempo_*.py          # Tempo service modules (~30 tools)
│   └── bp_toolkit.py       # Optional bp_toolkit tools (26)
├── agentbridge/            # HTTP client package (legacy)
├── tests/                  # Test files
├── scripts/                # Utility scripts
├── mcp_config.example.json # Example Claude Code config
├── requirements.txt
├── pyproject.toml
└── README.md
```

## MCP Server Configuration

Copy `mcp_config.example.json` and update paths for your project:

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

**Note:** `cwd` is `AgentBridge/` (parent of `mcp/`), not `AgentBridge/mcp/`.

---

## Testing

```bash
# From AgentBridge plugin root (parent of mcp/)
cd /path/to/YourProject/Plugins/AgentBridge

# Run tests (auto-detection finds Tempo)
python -m pytest mcp/tests/

# Or with explicit path
TEMPO_API_PATH="/path/to/Tempo/TempoCore/Content/Python/API/tempo" \
  python -m pytest mcp/tests/

# Quick import check
python -c "from mcp.services import agentbridge; print('OK')"
```

---

## Adding New Service Modules

1. Create `services/my_service.py`:

```python
from . import register_service, ServiceModule
from .base import create_channel, safe_call

TOOLS = [
    {
        "name": "my_tool",
        "description": "Does something",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
]

class MyClient:
    def __init__(self, host, port):
        self.channel = create_channel(host, port)
        self.stub = MyServiceStub(self.channel)

def connect(host, port): return MyClient(host, port)

def execute(client, tool_name, args):
    return json.dumps({"success": True})

register_service(ServiceModule(
    name="my_service",
    description="My service",
    tools=TOOLS,
    execute=execute,
    connect=connect,
))
```

2. Import in `services/__init__.py`:
```python
from . import my_service  # in _auto_register()
```

---

## bp_toolkit Integration

The `bp_toolkit.py` service conditionally loads when the bp_toolkit submodule is present.

**Path resolution:** `bp_toolkit.py` looks for `../bp_toolkit/` relative to the mcp package:
```
AgentBridge/
├── mcp/                    # This repo
│   └── services/
│       └── bp_toolkit.py   # Looks for ../../bp_toolkit/
└── bp_toolkit/             # Sibling submodule
```

If you move this repo, update the path in `_find_bp_toolkit()`.

---

## Help System

The MCP server has a self-documenting help system:

```python
help()                        # Overview
help(topic="actors")          # Actor operations
help(topic="properties")      # Property access
help(topic="classes")         # Type discovery
help(topic="assets")          # Asset/file operations
help(topic="workflows")       # Common workflows (includes PCG biome)
help(topic="bp_toolkit")      # Offline asset manipulation (if available)
```

### Keeping Help In Sync

When adding/modifying MCP tools, update `_get_help_text()` in `agentbridge.py`.

---

## Key Patterns

### Component Names in Property Paths

Use INSTANCE names (like `LightComponent0`), not CLASS names:

```python
# Wrong - class name won't work
get_property(actor="MyLight", path="PointLightComponent.Intensity")

# Correct - use instance name
get_property(actor="MyLight", path="LightComponent0.Intensity")
```

### DataAsset Properties

Property access works with DataAssets using asset paths as `actor_id`:

```python
get_property(actor_id="/Game/Biomes/ForestBiome.ForestBiome",
             path="BiomeDefinition.BiomeName")
```

### Arrays with Object References

Arrays of structs containing object refs require a two-step process:

```python
# Step 1: Create array elements with simple properties
set_property(actor_id="/Game/Biomes/TreeAssets.TreeAssets",
             path="BiomeAssets",
             value='[{"Enabled":true, "Weight":1.0}]')

# Step 2: Set object references individually
set_property(actor_id="/Game/Biomes/TreeAssets.TreeAssets",
             path="BiomeAssets[0].Mesh",
             value="/Game/Foliage/SM_Tree.SM_Tree")
```

---

## Related Repos

| Repo | Purpose |
|------|---------|
| AgentBridge | Unreal C++ plugin (parent repo) |
| bp_toolkit | Offline Blueprint/PCG manipulation |
| [Tempo](https://github.com/tempo-sim/Tempo) | gRPC infrastructure for Unreal |

---

## Todos

- [ ] Unified property setter (auto-detect type, route correctly)

## Stretch Goals

| Feature | Effort | Notes |
|---------|--------|-------|
| Sound capture | Medium | TempoAudio integration |
| Graph editing help | Low | Document manual graph editing workflows |
| Sequencer help | Low | Document Tempo sequencer tools |
