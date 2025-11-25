"""RHDH Plugin Store Manager Agent.

An expert agent for Red Hat Developer Hub's plugin ecosystem, providing:
- Plugin discovery and availability guidance
- Migration and building support
- Certification program management
- Plugin lifecycle and maintenance coordination
- Support boundary clarification
- Release planning assistance
- Metadata and registry management
- Team coordination guidance

Features:
- RAG knowledge base with comprehensive RHDH documentation
- Read-only Jira access to RHIDP and RHDHPLAN projects
- Environment-based configuration (no per-user setup)
"""

from typing import Any

from agno.db.sqlite import SqliteDb

from agentllm.agents.base import AgentFactory, BaseAgentWrapper
from agentllm.db import TokenStorage

from .store_manager_agent_configurator import StoreManagerAgentConfigurator


class StoreManagerAgent(BaseAgentWrapper):
    """RHDH Plugin Store Manager agent wrapper.

    Handles execution interface and delegates configuration to
    StoreManagerAgentConfigurator.
    """

    def __init__(
        self,
        shared_db: SqliteDb,
        token_storage: TokenStorage,
        user_id: str,
        session_id: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **model_kwargs,
    ):
        """Initialize the Store Manager Agent with configurator pattern.

        Args:
            shared_db: Shared database instance for session management
            token_storage: Token storage instance for credentials
            user_id: User identifier (wrapper is per-user+session)
            session_id: Session identifier (optional)
            temperature: Model temperature (0.0-2.0)
            max_tokens: Maximum tokens in response
            **model_kwargs: Additional model parameters
        """
        # Store token_storage for configurator
        self._token_storage = token_storage

        # Call parent constructor (will call _create_configurator)
        super().__init__(
            shared_db=shared_db,
            user_id=user_id,
            session_id=session_id,
            temperature=temperature,
            max_tokens=max_tokens,
            **model_kwargs,
        )

    def _create_configurator(
        self,
        user_id: str,
        session_id: str | None,
        shared_db: SqliteDb,
        **kwargs: Any,
    ) -> StoreManagerAgentConfigurator:
        """Create configurator for Store Manager agent.

        Args:
            user_id: User identifier
            session_id: Session identifier
            shared_db: Shared database
            **kwargs: Additional configurator arguments

        Returns:
            StoreManagerAgentConfigurator: Configured configurator instance
        """
        return StoreManagerAgentConfigurator(
            user_id=user_id,
            session_id=session_id,
            shared_db=shared_db,
            token_storage=self._token_storage,
            **kwargs,
        )


class StoreManagerAgentFactory(AgentFactory):
    """Factory for Store Manager agent creation.

    Implements the AgentFactory interface for plugin system registration.
    """

    @staticmethod
    def create_agent(
        shared_db: Any,
        token_storage: Any,
        user_id: str,
        session_id: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> StoreManagerAgent:
        """Create a Store Manager agent instance.

        Args:
            shared_db: Shared database instance
            token_storage: Token storage instance
            user_id: User identifier
            session_id: Optional session identifier
            temperature: Optional model temperature override
            max_tokens: Optional max tokens override
            **kwargs: Additional agent arguments

        Returns:
            StoreManagerAgent: Configured agent instance
        """
        return StoreManagerAgent(
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
        """Get agent metadata for registration.

        Returns:
            dict: Agent metadata including name, description, mode, and requirements
        """
        return {
            "name": "store-manager",
            "description": "RHDH Plugin Store Manager for catalog management, certification, and plugin lifecycle",
            "mode": "chat",
            "requires_env": ["GEMINI_API_KEY", "STORE_MANAGER_JIRA_API_TOKEN"],
        }
