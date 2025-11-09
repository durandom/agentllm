"""Example Agno agents for testing the LiteLLM provider."""

from typing import Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.openrouter import OpenRouter


def create_echo_agent(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    db=None,
    **model_kwargs,
) -> Agent:
    """Create a simple echo agent that repeats back what it receives.

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
        name="echo",
        model=OpenRouter(id="gpt-5-mini"),
        description="A simple agent that echoes back messages",
        instructions=[
            "You are a helpful assistant that echoes back what users say.",
            "Always be friendly and polite.",
        ],
        markdown=True,
        # Session management
        db=db,
        add_history_to_context=True,
        num_history_runs=10,  # Include last 10 messages
        read_chat_history=True,  # Allow agent to read full history
    )


def create_assistant_agent(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    db=None,
    **model_kwargs,
) -> Agent:
    """Create a general-purpose assistant agent.

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
        name="assistant",
        model=OpenAIChat(**model_params),
        description="A helpful general-purpose assistant",
        instructions=[
            "You are a helpful AI assistant.",
            "Provide clear, concise, and accurate responses.",
            "Be friendly and professional.",
        ],
        markdown=True,
        # Session management
        db=db,
        add_history_to_context=True,
        num_history_runs=10,  # Include last 10 messages
        read_chat_history=True,  # Allow agent to read full history
    )


def create_code_agent(
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    db=None,
    **model_kwargs,
) -> Agent:
    """Create a coding assistant agent.

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
        name="code-helper",
        model=OpenAIChat(**model_params),
        description="A coding assistant that helps with programming tasks",
        instructions=[
            "You are an expert programming assistant.",
            "Help users with code, debugging, and technical questions.",
            "Provide code examples when appropriate.",
            "Explain concepts clearly.",
        ],
        markdown=True,
        # Session management
        db=db,
        add_history_to_context=True,
        num_history_runs=10,  # Include last 10 messages
        read_chat_history=True,  # Allow agent to read full history
    )
