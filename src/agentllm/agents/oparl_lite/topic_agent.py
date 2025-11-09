"""OParl topic summary agent."""

from typing import Optional

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.mcp_toolbox import MCPToolbox


async def create_oparl_topic_summary(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    db=None,
    mcp_server_url: str = "https://oparl.bonn.machdenstaat.de/mcp",
    mcp_toolsets: Optional[list[str]] = None,
    **model_kwargs,
) -> Agent:
    """Create an OParl topic summary agent with MCP tools.

    Args:
        temperature: Model temperature (0.0-2.0)
        max_tokens: Maximum tokens in response
        db: Database instance for session management
        mcp_server_url: URL of the MCP server (default: OParl Bonn MCP server)
        mcp_toolsets: List of specific toolsets to load from MCP server (default: None = all tools)
        **model_kwargs: Additional model parameters

    Returns:
        Agent: Configured OParl topic summary agent with MCP tools
    """
    # Initialize MCPToolbox with the OParl MCP server
    async with MCPToolbox(
        url=mcp_server_url,
        toolsets=mcp_toolsets,
    ) as toolbox:
        # Build model parameters
        model_params = {}
        if temperature is not None:
            model_params["temperature"] = temperature
        if max_tokens is not None:
            model_params["max_tokens"] = max_tokens
        model_params.update(model_kwargs)

        return Agent(
            name="oparl-topic-summary",
            model=Claude(**model_params),
            description="An agent that summarizes OParl topics",
            instructions=[
                "You are an expert at analyzing and summarizing OParl data.",
                "Provide clear and concise summaries of topics.",
                "Use the available MCP tools to query and retrieve OParl data as needed.",
            ],
            tools=[toolbox],
            markdown=True,
            db=db,
            add_history_to_context=True,
            num_history_runs=10,
            read_chat_history=True,
        )
