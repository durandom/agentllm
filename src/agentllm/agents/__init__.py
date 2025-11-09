"""This is the agent registry."""

import inspect
from functools import partial
from pathlib import Path
from typing import Optional

from agno.agent import Agent
from agno.db.sqlite import SqliteDb

from agentllm.agents.examples import (
    create_assistant_agent,
    create_code_agent,
    create_echo_agent,
)
from agentllm.agents.oparl_lite import create_oparl_topic_summary

DB_PATH = Path("tmp/agno_sessions.db")
DB_PATH.parent.mkdir(exist_ok=True)

shared_db = SqliteDb(db_file=str(DB_PATH))


# Registry of available agents with shared_db pre-bound
AGENT_REGISTRY = {
    "echo": partial(create_echo_agent, db=shared_db),
    "assistant": partial(create_assistant_agent, db=shared_db),
    "code-helper": partial(create_code_agent, db=shared_db),
    "oparl-topic-summary": partial(create_oparl_topic_summary, db=shared_db),
}


async def _get_agent(
    agent_name: str,
    agent_registry: dict,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    db=None,
    **model_kwargs,
) -> Agent:
    """Get an agent by name with optional model parameters.

    Args:
        agent_name: The name of the agent to retrieve
        agent_registry: Registry mapping agent names to creator functions
        temperature: Model temperature (0.0-2.0)
        max_tokens: Maximum tokens in response
        db: Database instance for session management
        **model_kwargs: Additional model parameters

    Returns:
        Agent instance

    Raises:
        KeyError: If the agent name is not found
    """
    if agent_name not in agent_registry:
        raise KeyError(
            f"Agent '{agent_name}' not found. Available agents: {', '.join(agent_registry.keys())}"
        )

    creator_func = agent_registry[agent_name]

    # Check if the creator function is async and call accordingly
    if inspect.iscoroutinefunction(
        creator_func.func if isinstance(creator_func, partial) else creator_func
    ):
        return await creator_func(
            temperature=temperature, max_tokens=max_tokens, db=db, **model_kwargs
        )
    else:
        return creator_func(
            temperature=temperature, max_tokens=max_tokens, db=db, **model_kwargs
        )


async def get_agent(
    agent_name: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    **model_kwargs,
) -> Agent:
    """Get an agent by name with optional model parameters.

    Args:
        agent_name: The name of the agent to retrieve
        temperature: Model temperature (0.0-2.0)
        max_tokens: Maximum tokens in response
        **model_kwargs: Additional model parameters

    Returns:
        Agent instance

    Raises:
        KeyError: If the agent name is not found
    """
    return await _get_agent(
        agent_name=agent_name,
        agent_registry=AGENT_REGISTRY,
        temperature=temperature,
        max_tokens=max_tokens,
        db=shared_db,
        **model_kwargs,
    )
