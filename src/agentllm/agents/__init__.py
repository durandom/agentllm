"""This is the agent registry."""

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
from agentllm.agents.examples import get_agent as _get_agent
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


def get_agent(
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
    return _get_agent(
        agent_name=agent_name,
        agent_registry=AGENT_REGISTRY,
        temperature=temperature,
        max_tokens=max_tokens,
        db=shared_db,
        **model_kwargs,
    )
