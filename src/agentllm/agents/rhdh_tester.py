"""RHDH Tester Agent - Creates and configures Red Hat Developer Hub test instances."""

from typing import Any

from agno.db.sqlite import SqliteDb

from agentllm.agents.base import AgentFactory, BaseAgentWrapper
from agentllm.agents.rhdh_tester_configurator import RHDHTesterConfigurator


class RHDHTesterAgent(BaseAgentWrapper):
    """RHDH Tester Agent.

    Creates and configures Red Hat Developer Hub test instances by automating
    the PR workflow in the redhat-developer/rhdh-test-instance repository.
    """

    def _create_configurator(
        self,
        user_id: str,
        session_id: str | None,
        shared_db: SqliteDb,
        **kwargs: Any,
    ) -> RHDHTesterConfigurator:
        """Create the configurator for this agent.

        Args:
            user_id: User identifier
            session_id: Session identifier
            shared_db: Shared database
            **kwargs: Additional arguments

        Returns:
            RHDHTesterConfigurator instance
        """
        # Extract token_storage, temperature, and max_tokens from kwargs
        # These are passed via BaseAgentWrapper.__init__ -> _create_configurator
        token_storage = kwargs.pop("token_storage", None)
        temperature = kwargs.pop("temperature", None)
        max_tokens = kwargs.pop("max_tokens", None)

        return RHDHTesterConfigurator(
            user_id=user_id,
            session_id=session_id,
            shared_db=shared_db,
            token_storage=token_storage,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )


class RHDHTesterFactory(AgentFactory):
    """Factory for creating RHDH Tester Agent instances."""

    @staticmethod
    def create_agent(
        shared_db: SqliteDb,
        token_storage: Any,
        user_id: str,
        session_id: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> RHDHTesterAgent:
        """Create an RHDH Tester Agent instance.

        Args:
            shared_db: Shared database
            token_storage: Token storage
            user_id: User identifier
            session_id: Session identifier
            temperature: Temperature for model
            max_tokens: Max tokens for model
            **kwargs: Additional arguments

        Returns:
            RHDHTesterAgent instance
        """
        return RHDHTesterAgent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id=user_id,
            session_id=session_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    @staticmethod
    def get_metadata() -> dict[str, Any]:
        """Get agent metadata.

        Returns:
            Dictionary containing agent metadata
        """
        return {
            "name": "rhdh-tester",
            "description": "RHDH/Backstage test instance creator with intelligent config merging",
            "mode": "chat",
            "requires_env": ["GEMINI_API_KEY"],
        }

