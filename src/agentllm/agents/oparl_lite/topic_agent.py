"""OParl topic summary agent."""

from typing import Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat


def create_oparl_topic_summary(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    db=None,
    **model_kwargs,
) -> Agent:
    """Create an OParl topic summary agent.

    Args:
        temperature: Model temperature (0.0-2.0)
        max_tokens: Maximum tokens in response
        db: Database instance for session management
        **model_kwargs: Additional model parameters
    """
    model_params = {"id": "gpt-4o-mini"}
    if temperature is not None:
        model_params["temperature"] = temperature
    if max_tokens is not None:
        model_params["max_tokens"] = max_tokens
    model_params.update(model_kwargs)

    return Agent(
        name="oparl-topic-summary",
        model=OpenAIChat(**model_params),
        description="An agent that summarizes OParl topics",
        instructions=[
            "You are an expert at analyzing and summarizing OParl data.",
            "Provide clear and concise summaries of topics.",
        ],
        markdown=True,
        db=db,
        add_history_to_context=True,
        num_history_runs=10,
        read_chat_history=True,
    )
