"""
Base utilities for service modules.
"""

import grpc
import sys
import os
from pathlib import Path
from typing import Optional


def _find_tempo_api_path() -> Optional[str]:
    """
    Find the Tempo API path for gRPC stubs.

    Resolution order:
    1. TEMPO_API_PATH environment variable
    2. Auto-detect relative to this file (Plugins/AgentBridge/mcp -> Plugins/Tempo/...)
    3. PYTHONPATH (if already set up externally)

    Returns the path if found, None otherwise.
    """
    # 1. Check environment variable
    env_path = os.environ.get("TEMPO_API_PATH")
    if env_path and os.path.isdir(env_path):
        return env_path

    # 2. Auto-detect relative to this file
    # This file is at: <Project>/Plugins/AgentBridge/mcp/services/base.py
    # Tempo API is at: <Project>/Plugins/Tempo/TempoCore/Content/Python/API/tempo
    try:
        this_file = Path(__file__).resolve()
        # Go up: services -> mcp -> AgentBridge -> Plugins
        plugins_dir = this_file.parent.parent.parent.parent
        tempo_api = plugins_dir / "Tempo" / "TempoCore" / "Content" / "Python" / "API" / "tempo"
        if tempo_api.is_dir():
            return str(tempo_api)
    except Exception:
        pass

    # 3. Check if stubs are already importable (PYTHONPATH set externally)
    try:
        import TempoScripting
        return None  # Already available, no path needed
    except ImportError:
        pass

    return None


def _setup_tempo_path():
    """Set up the Python path for Tempo API imports."""
    tempo_path = _find_tempo_api_path()
    if tempo_path and tempo_path not in sys.path:
        sys.path.insert(0, tempo_path)
    elif tempo_path is None:
        # Check if imports work anyway
        try:
            import TempoScripting
        except ImportError:
            import warnings
            warnings.warn(
                "Could not find Tempo API path. Set TEMPO_API_PATH environment variable "
                "or ensure Tempo plugin is installed at ../Tempo/ relative to AgentBridge."
            )


# Initialize path on module load
_setup_tempo_path()


def create_channel(host: str = "localhost", port: int = 50051) -> grpc.Channel:
    """Create a gRPC channel to the Tempo server."""
    return grpc.insecure_channel(f"{host}:{port}")


def safe_call(func, *args, **kwargs):
    """Wrap a gRPC call with error handling."""
    try:
        return func(*args, **kwargs)
    except grpc.RpcError as e:
        return {"error": f"gRPC error: {e.code().name} - {e.details()}"}
    except Exception as e:
        return {"error": str(e)}
