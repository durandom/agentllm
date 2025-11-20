"""Tests for RHDH Tester Agent and extended GitHub Toolkit."""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest
from agno.db.sqlite import SqliteDb
from agentllm.agents.rhdh_tester import RHDHTesterAgent, RHDHTesterFactory
from agentllm.agents.rhdh_tester_configurator import RHDHTesterConfigurator
from agentllm.tools.github_toolkit import GitHubToolkit


class TestGitHubToolkitExtensions:
    """Test extended GitHub Toolkit functionality (file/branch/PR operations)."""

    def setup_method(self):
        """Setup toolkit with mock token."""
        self.toolkit = GitHubToolkit(token="fake_token")
        self.repo = "owner/repo"

    @patch("requests.get")
    def test_get_file(self, mock_get):
        """Test reading file content."""
        # Mock response
        content = "test content"
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": encoded_content}
        mock_get.return_value = mock_response

        # Call method
        result = self.toolkit.get_file(self.repo, "path/to/file.yaml")

        # Verify
        assert result == content
        mock_get.assert_called_with(
            "https://api.github.com/repos/owner/repo/contents/path/to/file.yaml",
            headers=self.toolkit._headers,
            params={"ref": "main"},
            timeout=30,
        )

    @patch("requests.get")
    def test_get_branch_info(self, mock_get):
        """Test getting branch info."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "main",
            "commit": {"sha": "sha123"},
            "protected": True,
        }
        mock_get.return_value = mock_response

        result = self.toolkit.get_branch_info(self.repo, "main")
        data = json.loads(result)

        assert data["name"] == "main"
        assert data["sha"] == "sha123"
        assert data["protected"] is True

    @patch("requests.post")
    @patch("requests.get")
    def test_create_branch(self, mock_get, mock_post):
        """Test creating a new branch."""
        # Mock base branch info
        mock_get_response = MagicMock()
        mock_get_response.status_code = 200
        mock_get_response.json.return_value = {
            "name": "main",
            "commit": {"sha": "base_sha"},
        }
        mock_get.return_value = mock_get_response

        # Mock create response
        mock_post_response = MagicMock()
        mock_post_response.status_code = 201
        mock_post.return_value = mock_post_response

        result = self.toolkit.create_branch(self.repo, "main", "new-branch")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["sha"] == "base_sha"

        # Verify API call
        mock_post.assert_called_with(
            "https://api.github.com/repos/owner/repo/git/refs",
            headers=self.toolkit._headers,
            json={"ref": "refs/heads/new-branch", "sha": "base_sha"},
            timeout=30,
        )

    @patch("requests.put")
    @patch("requests.get")
    def test_create_or_update_file(self, mock_get, mock_put):
        """Test creating/updating a file."""
        # Mock existing file check (fail = create new)
        mock_get_response = MagicMock()
        mock_get_response.status_code = 404
        mock_get.return_value = mock_get_response

        # Mock put response
        mock_put_response = MagicMock()
        mock_put_response.status_code = 201
        mock_put_response.json.return_value = {
            "content": {"path": "file.txt"},
            "commit": {"sha": "new_sha"},
        }
        mock_put.return_value = mock_put_response

        content = "new content"
        result = self.toolkit.create_or_update_file(
            self.repo, "main", "file.txt", content, "Add file"
        )
        data = json.loads(result)

        assert data["status"] == "success"

        # Verify API call
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        mock_put.assert_called_with(
            "https://api.github.com/repos/owner/repo/contents/file.txt",
            headers=self.toolkit._headers,
            json={
                "message": "Add file",
                "content": encoded_content,
                "branch": "main",
            },
            timeout=30,
        )

    @patch("requests.post")
    def test_create_pull_request(self, mock_post):
        """Test creating a PR."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": 123,
            "html_url": "http://github.com/owner/repo/pull/123",
            "title": "Test PR",
        }
        mock_post.return_value = mock_response

        result = self.toolkit.create_pull_request(
            self.repo, "feature", "main", "Test PR", "Description"
        )
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["number"] == 123

        mock_post.assert_called_with(
            "https://api.github.com/repos/owner/repo/pulls",
            headers=self.toolkit._headers,
            json={
                "title": "Test PR",
                "body": "Description",
                "head": "feature",
                "base": "main",
            },
            timeout=30,
        )

    @patch("requests.post")
    def test_add_pr_comment(self, mock_post):
        """Test adding a PR comment."""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_post.return_value = mock_response

        result = self.toolkit.add_pr_comment(self.repo, 123, "/test")
        data = json.loads(result)

        assert data["status"] == "success"

        mock_post.assert_called_with(
            "https://api.github.com/repos/owner/repo/issues/123/comments",
            headers=self.toolkit._headers,
            json={"body": "/test"},
            timeout=30,
        )

    @patch("requests.post")
    def test_sync_fork(self, mock_post):
        """Test syncing fork."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "Successfully fetched and merged"}
        mock_post.return_value = mock_response

        result = self.toolkit.sync_fork(self.repo, "main")
        data = json.loads(result)

        assert data["status"] == "success"
        
        mock_post.assert_called_with(
            "https://api.github.com/repos/owner/repo/merge-upstream",
            headers=self.toolkit._headers,
            json={"branch": "main"},
            timeout=30,
        )

    @patch("requests.post")
    def test_create_fork(self, mock_post):
        """Test creating fork."""
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.json.return_value = {
            "full_name": "user/repo",
            "html_url": "https://github.com/user/repo"
        }
        mock_post.return_value = mock_response

        result = self.toolkit.create_fork("original_owner", "repo")
        data = json.loads(result)

        assert data["status"] == "success"
        assert data["full_name"] == "user/repo"

        mock_post.assert_called_with(
            "https://api.github.com/repos/original_owner/repo/forks",
            headers=self.toolkit._headers,
            timeout=30,
        )

    @patch("requests.get")
    def test_get_user_forks(self, mock_get):
        """Test getting user forks."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "full_name": "user/target-repo",
                "owner": {"login": "user"},
                "name": "target-repo",
                "fork": True,
                "html_url": "https://github.com/user/target-repo"
            },
            {
                "full_name": "user/other-repo",
                "owner": {"login": "user"},
                "name": "other-repo",
                "fork": False,
                "html_url": "https://github.com/user/other-repo"
            }
        ]
        mock_get.return_value = mock_response

        result = self.toolkit.get_user_forks("target-repo")
        forks = json.loads(result)

        assert len(forks) == 1
        assert forks[0]["full_name"] == "user/target-repo"

        mock_get.assert_called_with(
            "https://api.github.com/user/repos",
            headers=self.toolkit._headers,
            params={"type": "public", "per_page": 100},
            timeout=30,
        )


class TestRHDHTesterConfigurator:
    """Test RHDH Tester Configurator."""

    def test_tool_subset_selection(self):
        """Test that configurator selects correct subset of tools."""
        configurator = RHDHTesterConfigurator(
            user_id="test_user",
            session_id="test_session",
            shared_db=MagicMock(),
            token_storage=MagicMock(),
        )

        configs = configurator._initialize_toolkit_configs()
        assert len(configs) == 1
        
        github_config = configs[0]
        # Verify tool subset
        expected_tools = [
            "get_file",
            "list_directory",
            "get_branch_info",
            "create_branch",
            "create_or_update_file",
            "create_pull_request",
            "add_pr_comment",
            "sync_fork",
            "create_fork",
            # "get_user_forks", # Removed as per user request
        ]
        assert github_config._tools == expected_tools

    def test_model_params(self):
        """Test model parameters configuration."""
        configurator = RHDHTesterConfigurator(
            user_id="test_user",
            session_id="test_session",
            shared_db=MagicMock(),
            token_storage=MagicMock(),
        )

        # Test get_model_id
        assert configurator._get_model_id() == "gemini-3-pro-preview"

        # Test build_model_params
        params = configurator._build_model_params()
        
        assert params["thinking_budget"] == 300
        assert params["include_thoughts"] is True
        assert params["temperature"] == 0.3
        assert params["id"] == "gemini-3-pro-preview"


class TestRHDHTesterAgent:
    """Test RHDH Tester Agent instantiation and execution."""

    def test_agent_instantiation(self):
        """Test that agent is instantiated correctly with all params."""
        shared_db = MagicMock(spec=SqliteDb)
        token_storage = MagicMock()
        
        # Create agent via factory (simulating custom_handler)
        agent = RHDHTesterFactory.create_agent(
            shared_db=shared_db,
            token_storage=token_storage,
            user_id="test_user",
            session_id="test_session",
            temperature=0.5,
            max_tokens=1000,
        )
        
        # Verify configurator was created with correct params
        configurator = agent._configurator
        assert isinstance(configurator, RHDHTesterConfigurator)
        assert configurator._token_storage == token_storage
        assert configurator._temperature == 0.5
        assert configurator._max_tokens == 1000
