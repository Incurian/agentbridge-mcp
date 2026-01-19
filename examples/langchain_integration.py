"""
LangChain Integration for AgentBridge MCP Server

This module demonstrates how to use the AgentBridge MCP tools with LangChain agents.
It uses the langchain-mcp-adapters package to connect via stdio transport.

Requirements:
    pip install langchain-mcp-adapters langgraph langchain-anthropic
    # or: pip install langchain-mcp-adapters langgraph langchain-openai

Usage:
    # Make sure Unreal Editor is running with AgentBridge plugin
    python -m mcp.examples.langchain_integration

    # Or with a custom query:
    python -m mcp.examples.langchain_integration "Spawn a PointLight at 0,0,500"
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

# Determine paths relative to this file
SCRIPT_DIR = Path(__file__).parent
MCP_DIR = SCRIPT_DIR.parent  # mcp/
AGENTBRIDGE_DIR = MCP_DIR.parent  # AgentBridge/
PROJECT_ROOT = AGENTBRIDGE_DIR.parent.parent  # TempoSample/

# Default paths - adjust these for your project
DEFAULT_PYTHON = PROJECT_ROOT / "TempoEnv" / "Scripts" / "python.exe"
DEFAULT_TEMPO_API = PROJECT_ROOT / "Plugins" / "Tempo" / "TempoCore" / "Content" / "Python" / "API" / "tempo"


def get_mcp_client_config(
    host: str = "localhost",
    port: int = 10001,
    profile: str = "full",
    python_path: Optional[Path] = None,
) -> dict:
    """
    Get the MCP client configuration for AgentBridge.

    Args:
        host: gRPC server host (where Unreal is running)
        port: gRPC server port (Tempo default is 10001)
        profile: MCP profile to load (core, standard, editor, simulation, full)
        python_path: Path to Python executable (defaults to TempoEnv)

    Returns:
        Configuration dict for MultiServerMCPClient
    """
    python_exe = python_path or DEFAULT_PYTHON

    # Build environment with Tempo API path
    env = os.environ.copy()
    if DEFAULT_TEMPO_API.exists():
        env["TEMPO_API_PATH"] = str(DEFAULT_TEMPO_API)

    return {
        "agentbridge": {
            "command": str(python_exe),
            "args": [
                "-m", "mcp",
                "--host", host,
                "--port", str(port),
                "--profile", profile,
            ],
            "cwd": str(AGENTBRIDGE_DIR),
            "transport": "stdio",
            "env": env,
        }
    }


async def create_agent(
    model: str = "claude-sonnet-4-20250514",
    provider: str = "anthropic",
    host: str = "localhost",
    port: int = 10001,
    profile: str = "full",
):
    """
    Create a LangChain agent with AgentBridge MCP tools.

    Args:
        model: Model name to use
        provider: "anthropic" or "openai"
        host: gRPC server host
        port: gRPC server port
        profile: MCP profile (core, standard, editor, simulation, full)

    Returns:
        Tuple of (agent, client) - client must be kept alive while agent is used
    """
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langgraph.prebuilt import create_react_agent

    # Create LLM based on provider
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        llm = ChatAnthropic(model=model)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        llm = ChatOpenAI(model=model)
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'anthropic' or 'openai'")

    # Create MCP client
    config = get_mcp_client_config(host=host, port=port, profile=profile)
    client = MultiServerMCPClient(config)

    # Connect and get tools
    await client.__aenter__()
    tools = await client.get_tools()
    print(f"Loaded {len(tools)} AgentBridge tools")

    # Create agent
    agent = create_react_agent(llm, tools)

    return agent, client


async def run_query(query: str, **agent_kwargs):
    """
    Run a single query against the AgentBridge MCP server.

    Args:
        query: Natural language query for the agent
        **agent_kwargs: Arguments passed to create_agent()

    Returns:
        Agent response
    """
    agent, client = await create_agent(**agent_kwargs)

    try:
        result = await agent.ainvoke({
            "messages": [("user", query)]
        })
        return result
    finally:
        await client.__aexit__(None, None, None)


async def interactive_session(**agent_kwargs):
    """
    Run an interactive session with the AgentBridge agent.

    Args:
        **agent_kwargs: Arguments passed to create_agent()
    """
    agent, client = await create_agent(**agent_kwargs)

    print("\n" + "="*60)
    print("AgentBridge Interactive Session")
    print("Type 'quit' or 'exit' to end the session")
    print("="*60 + "\n")

    try:
        while True:
            try:
                query = input("You: ").strip()
            except EOFError:
                break

            if not query:
                continue
            if query.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            try:
                result = await agent.ainvoke({
                    "messages": [("user", query)]
                })

                # Extract the final message
                messages = result.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, "content"):
                        print(f"\nAgent: {last_message.content}\n")
                    else:
                        print(f"\nAgent: {last_message}\n")

            except Exception as e:
                print(f"\nError: {e}\n")

    finally:
        await client.__aexit__(None, None, None)


# =============================================================================
# Example: Simple tool usage without full agent
# =============================================================================

async def simple_tool_example():
    """
    Demonstrates using MCP tools directly without a full agent.
    This is useful for programmatic access to specific tools.
    """
    from langchain_mcp_adapters.client import MultiServerMCPClient

    config = get_mcp_client_config(profile="standard")

    async with MultiServerMCPClient(config) as client:
        tools = await client.get_tools()

        # Find a specific tool
        query_actors_tool = next(
            (t for t in tools if t.name == "query_actors"),
            None
        )

        if query_actors_tool:
            # Call the tool directly
            result = await query_actors_tool.ainvoke({
                "class_name": "PointLight",
                "limit": 10
            })
            print(f"PointLights in scene: {result}")

        # Find and call help tool
        help_tool = next((t for t in tools if t.name == "help"), None)
        if help_tool:
            result = await help_tool.ainvoke({"topic": "actors"})
            print(f"Help:\n{result}")


# =============================================================================
# Example: Batch operations
# =============================================================================

async def batch_spawn_example():
    """
    Demonstrates spawning multiple actors programmatically.
    """
    from langchain_mcp_adapters.client import MultiServerMCPClient

    config = get_mcp_client_config(profile="standard")

    async with MultiServerMCPClient(config) as client:
        tools = await client.get_tools()

        spawn_tool = next((t for t in tools if t.name == "spawn_actor"), None)
        if not spawn_tool:
            print("spawn_actor tool not found")
            return

        # Spawn a grid of point lights
        for x in range(3):
            for y in range(3):
                result = await spawn_tool.ainvoke({
                    "class_name": "PointLight",
                    "location": [x * 200, y * 200, 300],
                    "label": f"GridLight_{x}_{y}"
                })
                print(f"Spawned: {result}")


# =============================================================================
# Main entry point
# =============================================================================

async def main():
    """Main entry point for the example."""
    import argparse

    parser = argparse.ArgumentParser(
        description="LangChain integration with AgentBridge MCP"
    )
    parser.add_argument(
        "query",
        nargs="?",
        default=None,
        help="Query to run (if not provided, starts interactive session)"
    )
    parser.add_argument(
        "--model",
        default="claude-sonnet-4-20250514",
        help="Model to use (default: claude-sonnet-4-20250514)"
    )
    parser.add_argument(
        "--provider",
        choices=["anthropic", "openai"],
        default="anthropic",
        help="LLM provider (default: anthropic)"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="gRPC server host (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=10001,
        help="gRPC server port (default: 10001)"
    )
    parser.add_argument(
        "--profile",
        default="full",
        help="MCP profile: core, standard, editor, simulation, full (default: full)"
    )
    parser.add_argument(
        "--example",
        choices=["simple", "batch"],
        help="Run a specific example instead of agent"
    )

    args = parser.parse_args()

    # Run specific examples
    if args.example == "simple":
        await simple_tool_example()
        return
    elif args.example == "batch":
        await batch_spawn_example()
        return

    # Agent kwargs
    agent_kwargs = {
        "model": args.model,
        "provider": args.provider,
        "host": args.host,
        "port": args.port,
        "profile": args.profile,
    }

    if args.query:
        # Single query mode
        result = await run_query(args.query, **agent_kwargs)
        messages = result.get("messages", [])
        if messages:
            print(messages[-1].content if hasattr(messages[-1], "content") else messages[-1])
    else:
        # Interactive mode
        await interactive_session(**agent_kwargs)


if __name__ == "__main__":
    asyncio.run(main())
