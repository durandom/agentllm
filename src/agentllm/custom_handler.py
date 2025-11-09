"""Custom LiteLLM handler for Agno provider using dynamic registration."""

import asyncio
import logging
import os
from collections.abc import AsyncIterator, Callable, Iterator
from pathlib import Path
from typing import Any, override

import litellm
from litellm.llms.custom_llm import CustomLLM
from litellm.types.utils import Choices, GenericStreamingChunk, Message, ModelResponse

# Configure logging for our custom handler
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Determine log file path - use temp directory
log_dir = os.getenv("AGENTLLM_DATA_DIR", "tmp")
log_file = Path(log_dir) / "agno_handler.log"

# File handler for detailed logs
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

# Console handler for important logs only
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter("[AGNO] %(levelname)s: %(message)s"))

logger.addHandler(file_handler)
logger.addHandler(console_handler)


class AgnoCustomLLM(CustomLLM):
    """Custom LiteLLM handler for Agno agents."""

    def __init__(self) -> None:
        """Initialize the custom LLM handler with agent cache."""
        super().__init__()
        # Cache agents by (agent_name, temperature, max_tokens, user_id)
        self._agent_cache: dict[tuple, Any] = {}
        logger.info("Initialized AgnoCustomLLM with agent caching")

    def _extract_session_info(self, kwargs: dict[str, Any]) -> tuple[str | None, str | None]:
        """Extract session_id and user_id from request kwargs.

        Checks multiple sources in priority order.
        """
        session_id = None
        user_id = None

        # 1. Check request body for metadata
        litellm_params = kwargs.get("litellm_params", {})
        proxy_request = litellm_params.get("proxy_server_request", {})
        request_body = proxy_request.get("body", {})
        body_metadata = request_body.get("metadata", {})

        if body_metadata:
            session_id = body_metadata.get("session_id") or body_metadata.get("chat_id")
            user_id = body_metadata.get("user_id")
            logger.info("Found in body metadata: session_id=%s, user_id=%s", session_id, user_id)

        # 2. Check OpenWebUI headers
        headers = litellm_params.get("metadata", {}).get("headers", {})
        if not session_id and headers:
            # Check for chat_id header
            session_id = headers.get("x-openwebui-chat-id") or headers.get("X-OpenWebUI-Chat-Id")
            logger.info("Found in headers: session_id=%s", session_id)

        if not user_id and headers:
            # Check for user_id header
            user_id = (
                headers.get("x-openwebui-user-id")
                or headers.get("X-OpenWebUI-User-Id")
                or headers.get("x-openwebui-user-email")
                or headers.get("X-OpenWebUI-User-Email")
            )
            logger.info("Found in headers: user_id=%s", user_id)

        # 3. Check LiteLLM metadata
        if not session_id and "litellm_params" in kwargs:
            litellm_metadata = litellm_params.get("metadata", {})
            session_id = litellm_metadata.get("session_id") or litellm_metadata.get(
                "conversation_id"
            )
            if session_id:
                logger.info("Found in LiteLLM metadata: session_id=%s", session_id)

        # 4. Fallback to user field
        if not user_id:
            user_id = kwargs.get("user")
            if user_id:
                logger.info("Found in user field: user_id=%s", user_id)

        # Log what we're using
        logger.info(
            "Final extracted session info: user_id=%s, session_id=%s",
            user_id,
            session_id,
        )

        # Log full structure for debugging (only if nothing found)
        if not session_id and not user_id:
            logger.warning("No session/user info found! Logging full request structure:")
            logger.warning("Headers available: %s", list(headers.keys()) if headers else "None")
            logger.warning(
                "Body metadata keys: %s",
                list(body_metadata.keys()) if body_metadata else "None",
            )
            logger.warning(
                "LiteLLM metadata keys: %s",
                list(litellm_params.get("metadata", {}).keys()),
            )

        return session_id, user_id

    def _get_agent(self, model: str, user_id: str | None = None, **kwargs) -> Any:
        """Get agent instance from model name with parameters.

        Uses caching to reuse agent instances for the same configuration and user.
        """
        # Extract agent name from model
        agent_name = model.replace("agno/", "")

        # Extract OpenAI parameters to pass to agent
        temperature = kwargs.get("temperature")
        max_tokens = kwargs.get("max_tokens")

        # Build cache key from agent configuration and user_id
        cache_key = (agent_name, temperature, max_tokens, user_id)

        # Check if agent exists in cache
        if cache_key in self._agent_cache:
            logger.info("Using cached agent for key: %s", cache_key)
            return self._agent_cache[cache_key]

        # Create new agent and cache it
        logger.info("Creating new agent for key: %s", cache_key)
        try:
            # Import get_agent at function scope to avoid top-level import
            import asyncio

            from agentllm.agents import get_agent, release_manager

            # Special handling for the ReleaseManager agent type
            if agent_name == "release-manager":
                agent = release_manager.ReleaseManager(
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            else:
                # Get the actual agent using async get_agent
                agent = asyncio.run(get_agent(agent_name, temperature=temperature, max_tokens=max_tokens))

            # Wrap the agent to support both sync and async calls
            class AgentWrapper:
                def __init__(self, agent):
                    self._agent = agent

                def run(self, *args, **kwargs):
                    # If ReleaseManager, call its run method directly
                    if hasattr(self._agent, 'run'):
                        return self._agent.run(*args, **kwargs)

                    # Fallback for other agents
                    return asyncio.run(self._agent.arun(*args, **kwargs))

                def __getattr__(self, name):
                    # Delegate other attributes to the original agent
                    return getattr(self._agent, name)

            # Wrap the agent
            wrapped_agent = AgentWrapper(agent)

            # Cache the wrapped agent
            self._agent_cache[cache_key] = wrapped_agent
            logger.info("Cached agent. Total cached agents: %s", len(self._agent_cache))
            return wrapped_agent
        except Exception as e:
            raise RuntimeError(f"Agent '{agent_name}' not found: {e}") from e

    def _build_response(self, model: str, content: str) -> ModelResponse:
        """Build a ModelResponse from agent output."""
        message = Message(role="assistant", content=content)
        choice = Choices(finish_reason="stop", index=0, message=message)

        model_response = ModelResponse()
        model_response.model = model
        model_response.choices = [choice]
        model_response.usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
        }

        return model_response

    def _extract_user_message(self, messages: list[dict[str, Any]]) -> str:
        """Extract the last user message from messages list."""
        # Find the last user message
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")

        # If no user message found, concatenate all messages
        return " ".join(msg.get("content", "") for msg in messages)

    @override
    def completion(
        self,
        model: str,
        messages: list[dict[str, Any]],
        api_base: str | None = None,
        custom_prompt_dict: dict[str, Any] | None = None,
        model_response: ModelResponse | None = None,
        print_verbose: Callable[[Any], None] | None = None,
        encoding: Any = None,
        api_key: str | None = None,
        logging_obj: Any = None,
        optional_params: dict[str, Any] | None = None,
        acompletion: Any = None,
        litellm_params: Any = None,
        logger_fn: Any = None,
        headers: Any = None,
        timeout: float | None = None,
        client: Any = None,
        *,
        custom_llm_provider: str = "agno",
        **kwargs,
    ) -> ModelResponse:
        """Handle completion requests for Agno agents."""
        logger.info("completion() called with model=%s", model)
        logger.info("kwargs: %s", kwargs)
        logger.info("messages: %s", messages)

        # Check if streaming is requested
        stream = kwargs.get("stream", False)
        if stream:
            # Return streaming iterator
            return next(
                iter(
                    self.streaming(
                        model=model,
                        messages=messages,
                        api_base=api_base,
                        custom_llm_provider=custom_llm_provider,
                        **kwargs,
                    )
                )
            )

        # Extract request parameters first (need user_id for agent cache)
        user_message = self._extract_user_message(messages)
        session_id, user_id = self._extract_session_info(kwargs)

        # Get agent instance
        agent = self._get_agent(model, user_id=user_id, **kwargs)

        # Run the agent with session management
        response = agent.run(user_message, stream=False, session_id=session_id, user_id=user_id)

        # Extract content and build response
        content = response.content if hasattr(response, "content") else str(response)
        return self._build_response(model, str(content))

    @override
    def streaming(
        self,
        model: str,
        messages: list[dict[str, Any]],
        api_base: str | None = None,
        custom_prompt_dict: dict[str, Any] | None = None,
        model_response: ModelResponse | None = None,
        print_verbose: Callable[[Any], None] | None = None,
        encoding: Any = None,
        api_key: str | None = None,
        logging_obj: Any = None,
        optional_params: dict[str, Any] | None = None,
        acompletion: Any = None,
        litellm_params: Any = None,
        logger_fn: Any = None,
        headers: Any = None,
        timeout: float | None = None,
        client: Any = None,
        *,
        custom_llm_provider: str = "agno",
        **kwargs,
    ) -> Iterator[GenericStreamingChunk]:
        """Handle streaming requests for Agno agents."""
        # Get the complete response
        result = self.completion(
            model=model,
            messages=messages,
            api_base=api_base,
            custom_llm_provider=custom_llm_provider,
            **{k: v for k, v in kwargs.items() if k != "stream"},
        )

        # Extract content from the ModelResponse
        content = ""
        if result.choices and len(result.choices) > 0:
            content = result.choices[0].message.content or ""

        # Return as GenericStreamingChunk format
        yield {
            "text": content,
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "tool_use": None,
            "usage": {
                "completion_tokens": (
                    result.usage.get("completion_tokens", 0) if result.usage else 0
                ),
                "prompt_tokens": (result.usage.get("prompt_tokens", 0) if result.usage else 0),
                "total_tokens": (result.usage.get("total_tokens", 0) if result.usage else 0),
            },
        }

    @override
    async def acompletion(
        self,
        model: str,
        messages: list[dict[str, Any]],
        api_base: str | None = None,
        custom_prompt_dict: dict[str, Any] | None = None,
        model_response: ModelResponse | None = None,
        print_verbose: Callable[[Any], None] | None = None,
        encoding: Any = None,
        api_key: str | None = None,
        logging_obj: Any = None,
        optional_params: dict[str, Any] | None = None,
        acompletion: Any = None,
        litellm_params: Any = None,
        logger_fn: Any = None,
        headers: Any = None,
        timeout: float | None = None,
        client: Any = None,
        *,
        custom_llm_provider: str = "agno",
        **kwargs,
    ) -> ModelResponse:
        """Async completion using agent.arun()."""
        logger.info("acompletion() called with model=%s", model)
        logger.info("kwargs: %s", kwargs)
        logger.info("messages: %s", messages)

        # Extract request parameters first (need user_id for agent cache)
        user_message = self._extract_user_message(messages)
        session_id, user_id = self._extract_session_info(kwargs)

        # Get agent instance
        agent = await asyncio.to_thread(self._get_agent, model, user_id=user_id, **kwargs)

        # Run the agent asynchronously with session management
        response = await agent.run(
            user_message, stream=False, session_id=session_id, user_id=user_id
        )

        # Extract content and build response
        content = response.content if hasattr(response, "content") else str(response)
        return self._build_response(model, str(content))

    @override
    async def astreaming(
        self,
        model: str,
        messages: list[dict[str, Any]],
        api_base: str | None = None,
        custom_prompt_dict: dict[str, Any] | None = None,
        model_response: ModelResponse | None = None,
        print_verbose: Callable[[Any], None] | None = None,
        encoding: Any = None,
        api_key: str | None = None,
        logging_obj: Any = None,
        optional_params: dict[str, Any] | None = None,
        acompletion: Any = None,
        litellm_params: Any = None,
        logger_fn: Any = None,
        headers: Any = None,
        timeout: float | None = None,
        client: Any = None,
        *,
        custom_llm_provider: str = "agno",
        **kwargs,
    ) -> AsyncIterator[GenericStreamingChunk]:
        """Async streaming using Agno's native streaming support."""
        logger.info("astreaming() called with model=%s", model)
        logger.info("kwargs: %s", kwargs)
        logger.info("messages: %s", messages)

        # Extract request parameters first (need user_id for agent cache)
        user_message = self._extract_user_message(messages)
        session_id, user_id = self._extract_session_info(kwargs)

        # Get agent instance
        agent = await asyncio.to_thread(self._get_agent, model, user_id=user_id, **kwargs)

        # Use Agno's real async streaming with session management
        chunk_count = 0

        async for chunk in agent.arun(
            user_message, stream=True, session_id=session_id, user_id=user_id
        ):
            # Extract content from chunk
            content = chunk.content if hasattr(chunk, "content") else str(chunk)

            if not content:
                continue

            # Yield GenericStreamingChunk format
            yield {
                "text": content,
                "finish_reason": None,
                "index": 0,
                "is_finished": False,
                "tool_use": None,
                "usage": {
                    "completion_tokens": 0,
                    "prompt_tokens": 0,
                    "total_tokens": 0,
                },
            }
            chunk_count += 1

        # Send final chunk with finish_reason
        yield {
            "text": "",
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "tool_use": None,
            "usage": {
                "completion_tokens": chunk_count,
                "prompt_tokens": 0,
                "total_tokens": chunk_count,
            },
        }


# Create a singleton instance
agno_handler = AgnoCustomLLM()


def register_agno_provider():
    """Register the Agno provider with LiteLLM."""
    litellm.custom_provider_map = [{"provider": "agno", "custom_handler": agno_handler}]
    print("✅ Registered Agno provider with LiteLLM")


if __name__ == "__main__":
    # Auto-register when run as script
    register_agno_provider()
    print("\n🚀 Agno provider registered!")
    print("   You can now use models like: agno/release-manager")
