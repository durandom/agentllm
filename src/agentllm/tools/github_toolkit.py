"""
GitHub toolkit for PR review prioritization and repository management.
"""

import base64
import json
from datetime import UTC, datetime
from typing import Any

import requests
from agno.tools import Toolkit
from loguru import logger


class GitHubToolkit(Toolkit):
    """Toolkit for GitHub PR review prioritization and management.

    This toolkit wraps Agno's GithubTools and adds review-specific functionality:
    - PR prioritization using multi-factor scoring
    - Review queue management
    - Repository velocity tracking
    - Smart review suggestions
    - File and branch management
    - PR creation and commenting
    - Fork management (create, sync, list)
    - User information
    """

    def __init__(
        self,
        token: str,
        server_url: str = "https://api.github.com",
        tools: list[str] | None = None,
        **kwargs,
    ):
        """Initialize GitHub toolkit with credentials.

        Args:
            token: GitHub personal access token
            server_url: GitHub API server URL (default: https://api.github.com)
            tools: Optional list of tool names to expose. If None, exposes all tools.
            **kwargs: Additional arguments passed to parent Toolkit
        """
        self._token = token
        self._server_url = server_url

        # Setup headers for GitHub API requests
        self._headers = {
            "Authorization": f"token {self._token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Map of all available tools
        all_tools = {
            "list_prs": self.list_prs,
            "prioritize_prs": self.prioritize_prs,
            "suggest_next_review": self.suggest_next_review,
            "get_repo_velocity": self.get_repo_velocity,
            "get_file": self.get_file,
            "list_directory": self.list_directory,
            "get_branch_info": self.get_branch_info,
            "create_branch": self.create_branch,
            "create_or_update_file": self.create_or_update_file,
            "create_pull_request": self.create_pull_request,
            "add_pr_comment": self.add_pr_comment,
            "sync_fork": self.sync_fork,
            "create_fork": self.create_fork,
            "get_user_info": self.get_user_info,
        }

        # Select subset if specified, otherwise use all
        if tools is not None:
            selected_tools = [all_tools[name] for name in tools if name in all_tools]
        else:
            selected_tools = list(all_tools.values())

        super().__init__(name="github_tools", tools=selected_tools, **kwargs)

    def validate_connection(self) -> tuple[bool, str]:
        """Validate the GitHub connection by authenticating.

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            logger.debug(f"Validating GitHub connection to {self._server_url}")

            # Try to get authenticated user info
            response = requests.get(f"{self._server_url}/user", headers=self._headers, timeout=10)

            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get("login", "Unknown")
                logger.info(f"Successfully connected to GitHub as {username}")
                return True, f"Successfully connected to GitHub as @{username}"
            else:
                error_msg = f"GitHub authentication failed: {response.status_code} {response.text}"
                logger.error(error_msg)
                return False, error_msg

        except Exception as e:
            error_msg = f"Failed to connect to GitHub: {str(e)}"
            logger.error(error_msg)
            return False, error_msg

    def get_user_info(self) -> str:
        """Get information about the currently authenticated user.

        Returns:
            JSON string containing user information (login, name, email, html_url, etc.)
        """
        try:
            logger.info("Getting authenticated user info")
            url = f"{self._server_url}/user"
            response = requests.get(url, headers=self._headers, timeout=10)

            if response.status_code != 200:
                error_msg = f"GitHub API error: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

            user_data = response.json()
            
            # Filter to relevant fields
            info = {
                "login": user_data.get("login"),
                "name": user_data.get("name"),
                "email": user_data.get("email"),
                "html_url": user_data.get("html_url"),
                "type": user_data.get("type"),
                "company": user_data.get("company"),
                "location": user_data.get("location"),
            }
            
            return json.dumps(info, indent=2)

        except Exception as e:
            error_msg = f"Error getting user info: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def list_prs(self, repo: str, state: str = "open", limit: int = 20) -> str:
        """List pull requests in simple markdown format with high-level information.

        Returns a clean markdown list of PRs without scoring, perfect for quick overview.

        Args:
            repo: Repository in format "owner/repo"
            state: PR state - "open", "closed", or "all" (default: "open")
            limit: Maximum number of PRs to return (default: 20)

        Returns:
            Markdown formatted string with PR list
        """
        try:
            logger.info(f"Listing PRs for {repo} (state={state}, limit={limit})")

            # Parse owner and repo
            parts = repo.split("/")
            if len(parts) != 2:
                return "**Error**: Repository must be in format 'owner/repo'"

            owner, repo_name = parts

            # Fetch PRs using GitHub API
            url = f"{self._server_url}/repos/{owner}/{repo_name}/pulls"
            params = {"state": state, "per_page": min(limit, 100)}
            response = requests.get(url, headers=self._headers, params=params, timeout=30)

            if response.status_code != 200:
                error_msg = f"GitHub API error: {response.status_code} {response.text}"
                logger.error(error_msg)
                return f"**Error**: {error_msg}"

            pr_list = response.json()

            # Filter out drafts
            pr_list = [pr for pr in pr_list if not pr.get("draft", False)]

            if not pr_list:
                return f"## 📋 Pull Requests for `{repo}`\n\nNo {state} pull requests found."

            # Fetch detailed info for each PR to get additions/deletions
            detailed_prs = []
            for pr in pr_list[:limit]:  # Only fetch details for PRs we'll show
                pr_number = pr.get("number")
                detail_url = f"{self._server_url}/repos/{owner}/{repo_name}/pulls/{pr_number}"
                detail_response = requests.get(detail_url, headers=self._headers, timeout=10)

                if detail_response.status_code == 200:
                    detailed_prs.append(detail_response.json())
                else:
                    # Fallback to basic data if detail fetch fails
                    detailed_prs.append(pr)

            prs = detailed_prs

            # Build markdown output
            lines = [
                f"## 📋 Pull Requests for `{repo}`",
                "",
                f"Showing {len(prs)} of {len(pr_list)} {state} PRs",
                "",
            ]

            for pr in prs:
                # Calculate age
                created_at = pr.get("created_at", "")
                try:
                    created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    age_days = (datetime.now(UTC) - created).days
                    if age_days == 0:
                        age_str = "today"
                    elif age_days == 1:
                        age_str = "1 day ago"
                    else:
                        age_str = f"{age_days} days ago"
                except Exception:
                    age_str = "unknown"

                # Get size info (now available from detailed fetch)
                additions = pr.get("additions", 0)
                deletions = pr.get("deletions", 0)
                size = additions + deletions

                # Format size
                if size < 50:
                    size_emoji = "🟢"
                    size_label = "small"
                elif size < 200:
                    size_emoji = "🟡"
                    size_label = "medium"
                else:
                    size_emoji = "🔴"
                    size_label = "large"

                size_str = f"{size_emoji} {size_label} (+{additions}/-{deletions})"

                # Draft indicator
                draft_str = " 📝 DRAFT" if pr.get("draft", False) else ""

                # Build PR line
                number = pr.get("number")
                title = pr.get("title", "No title")
                user = pr.get("user", {})
                author = user.get("login", "unknown") if isinstance(user, dict) else str(user)
                url = pr.get("html_url", pr.get("url", ""))

                lines.append(f"### [#{number}]({url}) {title}{draft_str}")
                lines.append(f"**Author**: @{author} • **Size**: {size_str} • **Age**: {age_str}")
                lines.append("")

            result = "\n".join(lines)
            logger.info(f"Listed {len(prs)} PRs for {repo}")
            return result

        except Exception as e:
            error_msg = f"Error listing PRs for {repo}: {str(e)}"
            logger.error(error_msg)
            return f"**Error**: {error_msg}"

    def _get_review_queue(self, repo: str, state: str = "open", include_drafts: bool = False) -> str:
        """Fetch pull requests from a repository (internal helper).

        Args:
            repo: Repository in format "owner/repo"
            state: PR state - "open", "closed", or "all" (default: "open")
            include_drafts: Whether to include draft PRs (default: False)

        Returns:
            JSON string containing list of pull requests
        """
        try:
            logger.info(f"Fetching review queue for {repo} (state={state}, drafts={include_drafts})")

            # Parse owner and repo
            parts = repo.split("/")
            if len(parts) != 2:
                return json.dumps({"error": "Repository must be in format 'owner/repo'"})

            owner, repo_name = parts

            # Fetch PRs using GitHub API
            url = f"{self._server_url}/repos/{owner}/{repo_name}/pulls"
            params = {"state": state, "per_page": 100}
            response = requests.get(url, headers=self._headers, params=params, timeout=30)

            if response.status_code != 200:
                error_msg = f"GitHub API error: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

            pr_list = response.json()

            # Filter out drafts if requested
            if not include_drafts:
                pr_list = [pr for pr in pr_list if not pr.get("draft", False)]

            logger.info(f"Found {len(pr_list)} PRs for {repo}")
            logger.info(f"PR list: {pr_list}")

            return json.dumps(pr_list, indent=2)

        except Exception as e:
            error_msg = f"Error fetching review queue for {repo}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def prioritize_prs(self, repo: str, limit: int = 10) -> str:
        """Prioritize pull requests using multi-factor scoring.

        This method fetches open PRs and ranks them by priority using:
        - Age (25%): Older PRs get priority
        - Size (20%): Smaller PRs are easier to review
        - Activity (15%): Recent discussion suggests urgency
        - Labels (10%): urgent/hotfix/blocking boost priority
        - Author (10%): First-time contributors get attention

        Args:
            repo: Repository in format "owner/repo"
            limit: Maximum number of PRs to return (default: 10)

        Returns:
            JSON string with prioritized PRs and scores
        """
        try:
            logger.info(f"Prioritizing PRs for {repo} (limit={limit})")

            # Get review queue
            queue_json = self._get_review_queue(repo=repo, state="open", include_drafts=False)
            pr_list = json.loads(queue_json)

            if "error" in pr_list:
                return queue_json

            if not isinstance(pr_list, list):
                return json.dumps({"error": "Invalid PR list format"})

            # Calculate scores for each PR
            scored_prs = []
            for pr in pr_list:
                score_data = self._calculate_pr_score(pr, repo)
                scored_prs.append(
                    {
                        "number": pr.get("number"),
                        "title": pr.get("title"),
                        "author": pr.get("user", {}).get("login", "unknown"),
                        "url": pr.get("html_url"),
                        "created_at": pr.get("created_at"),
                        "updated_at": pr.get("updated_at"),
                        "draft": pr.get("draft", False),
                        "score": score_data["total_score"],
                        "priority_tier": score_data["priority_tier"],
                        "score_breakdown": score_data["breakdown"],
                    }
                )

            # Sort by score (descending)
            scored_prs.sort(key=lambda x: x["score"], reverse=True)

            # Limit results
            top_prs = scored_prs[:limit]

            result = {
                "repository": repo,
                "total_prs": len(pr_list),
                "prioritized_prs": top_prs,
                "scoring_algorithm": {
                    "factors": [
                        {"name": "age", "weight": "25%", "description": "Days since creation"},
                        {"name": "size", "weight": "20%", "description": "Inverse of changes"},
                        {"name": "activity", "weight": "15%", "description": "Comments/reviews"},
                        {"name": "labels", "weight": "10%", "description": "urgent/hotfix/blocking"},
                        {"name": "author", "weight": "10%", "description": "New contributor bonus"},
                    ],
                    "tiers": {
                        "CRITICAL": "65-80 (hotfixes, urgent, blocking)",
                        "HIGH": "50-64 (aged PRs, active discussion)",
                        "MEDIUM": "35-49 (standard PRs)",
                        "LOW": "0-34 (WIP, drafts)",
                    },
                },
            }

            logger.info(f"Prioritized {len(top_prs)} PRs for {repo}")
            return json.dumps(result, indent=2)

        except Exception as e:
            error_msg = f"Error prioritizing PRs for {repo}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def _get_pr_details_with_score(self, repo: str, pr_number: int) -> str:
        """Get detailed PR information with priority score (internal helper).

        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number

        Returns:
            JSON string with detailed PR info and priority score
        """
        try:
            logger.info(f"Getting PR details with score for {repo}#{pr_number}")

            # Parse owner and repo
            parts = repo.split("/")
            if len(parts) != 2:
                return json.dumps({"error": "Repository must be in format 'owner/repo'"})

            owner, repo_name = parts

            # Get PR details using GitHub API
            url = f"{self._server_url}/repos/{owner}/{repo_name}/pulls/{pr_number}"
            response = requests.get(url, headers=self._headers, timeout=30)

            if response.status_code != 200:
                error_msg = f"GitHub API error: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

            pr = response.json()

            # Get file changes
            files_url = f"{self._server_url}/repos/{owner}/{repo_name}/pulls/{pr_number}/files"
            files_response = requests.get(files_url, headers=self._headers, timeout=30)
            changes = files_response.json() if files_response.status_code == 200 else []

            # Calculate score
            score_data = self._calculate_pr_score(pr, repo)

            result = {
                "number": pr.get("number"),
                "title": pr.get("title"),
                "description": pr.get("body", ""),
                "author": pr.get("user", {}).get("login", "unknown"),
                "url": pr.get("html_url"),
                "state": pr.get("state"),
                "draft": pr.get("draft", False),
                "created_at": pr.get("created_at"),
                "updated_at": pr.get("updated_at"),
                "merged_at": pr.get("merged_at"),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
                "changed_files": pr.get("changed_files", 0),
                "comments": pr.get("comments", 0),
                "review_comments": pr.get("review_comments", 0),
                "labels": [label.get("name") for label in pr.get("labels", [])],
                "score": score_data["total_score"],
                "priority_tier": score_data["priority_tier"],
                "score_breakdown": score_data["breakdown"],
                "files_changed": [{"filename": f.get("filename"), "changes": f.get("changes", 0)} for f in changes[:10]],
            }

            logger.info(f"Retrieved PR details for {repo}#{pr_number} (score: {score_data['total_score']})")
            return json.dumps(result, indent=2)

        except Exception as e:
            error_msg = f"Error getting PR details for {repo}#{pr_number}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def suggest_next_review(self, repo: str, reviewer: str | None = None) -> str:
        """Suggest the next PR to review based on priority.

        Args:
            repo: Repository in format "owner/repo"
            reviewer: Optional GitHub username to check if already assigned

        Returns:
            JSON string with recommended PR and reasoning
        """
        try:
            logger.info(f"Suggesting next review for {repo} (reviewer={reviewer})")

            # Get prioritized PRs
            prioritized_json = self.prioritize_prs(repo=repo, limit=5)
            prioritized = json.loads(prioritized_json)

            if "error" in prioritized:
                return prioritized_json

            prs = prioritized.get("prioritized_prs", [])
            if not prs:
                return json.dumps(
                    {
                        "suggestion": None,
                        "message": f"No open pull requests found in {repo}",
                    }
                )

            # Get the highest priority PR
            top_pr = prs[0]

            result = {
                "suggestion": {
                    "number": top_pr["number"],
                    "title": top_pr["title"],
                    "url": top_pr["url"],
                    "author": top_pr["author"],
                    "score": top_pr["score"],
                    "priority_tier": top_pr["priority_tier"],
                },
                "reasoning": self._generate_review_reasoning(top_pr),
                "alternatives": prs[1:3] if len(prs) > 1 else [],
                "total_in_queue": prioritized.get("total_prs", 0),
            }

            logger.info(f"Suggested PR #{top_pr['number']} for review (score: {top_pr['score']})")
            return json.dumps(result, indent=2)

        except Exception as e:
            error_msg = f"Error suggesting next review for {repo}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def get_repo_velocity(self, repo: str, days: int = 7) -> str:
        """Get repository merge velocity metrics.

        Measures all PR merges in the repository regardless of author/team.

        Args:
            repo: Repository in format "owner/repo"
            days: Number of days to analyze (default: 7)

        Returns:
            JSON string with velocity metrics including total merged PRs,
            average time to merge, velocity per day, and recent merges
        """
        try:
            logger.info(f"Getting repo velocity for {repo} (last {days} days)")

            # Parse owner and repo
            parts = repo.split("/")
            if len(parts) != 2:
                return json.dumps({"error": "Repository must be in format 'owner/repo'"})

            owner, repo_name = parts

            # Get closed/merged PRs using GitHub API
            url = f"{self._server_url}/repos/{owner}/{repo_name}/pulls"
            params = {"state": "closed", "per_page": 100, "sort": "updated", "direction": "desc"}
            response = requests.get(url, headers=self._headers, params=params, timeout=30)

            if response.status_code != 200:
                error_msg = f"GitHub API error: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

            closed_prs = response.json()

            # Filter to last N days and calculate metrics
            cutoff_date = datetime.now(UTC).timestamp() - (days * 86400)
            recent_prs = []

            for pr in closed_prs:
                if pr.get("merged_at"):
                    merged_date = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                    if merged_date.timestamp() >= cutoff_date:
                        recent_prs.append(pr)

            # Calculate metrics
            total_merged = len(recent_prs)
            avg_time_to_merge = 0

            if total_merged > 0:
                total_seconds = 0
                for pr in recent_prs:
                    created = datetime.fromisoformat(pr["created_at"].replace("Z", "+00:00"))
                    merged = datetime.fromisoformat(pr["merged_at"].replace("Z", "+00:00"))
                    total_seconds += (merged - created).total_seconds()

                avg_time_to_merge = total_seconds / total_merged / 3600  # Convert to hours

            result = {
                "repository": repo,
                "period_days": days,
                "total_merged": total_merged,
                "avg_time_to_merge_hours": round(avg_time_to_merge, 2),
                "velocity_per_day": round(total_merged / days, 2),
                "recent_merges": [
                    {
                        "number": pr.get("number"),
                        "title": pr.get("title"),
                        "author": pr.get("user", {}).get("login"),
                        "merged_at": pr.get("merged_at"),
                    }
                    for pr in recent_prs[:10]  # Show last 10
                ],
            }

            logger.info(f"Repo velocity for {repo}: {total_merged} PRs merged in {days} days")
            return json.dumps(result, indent=2)

        except Exception as e:
            error_msg = f"Error getting repo velocity for {repo}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def get_file(self, repo: str, path: str, branch: str = "main") -> str:
        """Get file content from GitHub.

        Args:
            repo: Repository in format "owner/repo"
            path: File path in repository
            branch: Branch to read from (default: "main")

        Returns:
            Content of the file as string (UTF-8 decoded)
        """
        try:
            logger.info(f"Reading file {path} from {repo} on branch {branch}")

            parts = repo.split("/")
            if len(parts) != 2:
                return "**Error**: Repository must be in format 'owner/repo'"

            owner, repo_name = parts

            url = f"{self._server_url}/repos/{owner}/{repo_name}/contents/{path}"
            params = {"ref": branch}
            response = requests.get(url, headers=self._headers, params=params, timeout=30)

            if response.status_code != 200:
                error_msg = f"GitHub API error: {response.status_code} {response.text}"
                logger.error(error_msg)
                return f"**Error**: {error_msg}"

            data = response.json()
            content = base64.b64decode(data["content"]).decode("utf-8")
            return content

        except Exception as e:
            error_msg = f"Error reading file {path}: {str(e)}"
            logger.error(error_msg)
            return f"**Error**: {error_msg}"

    def list_directory(self, repo: str, path: str, branch: str = "main") -> str:
        """List directory contents from GitHub.

        Args:
            repo: Repository in format "owner/repo"
            path: Directory path in repository
            branch: Branch to read from (default: "main")

        Returns:
            JSON string containing list of files/directories
        """
        try:
            logger.info(f"Listing directory {path} from {repo} on branch {branch}")

            parts = repo.split("/")
            if len(parts) != 2:
                return json.dumps({"error": "Repository must be in format 'owner/repo'"})

            owner, repo_name = parts

            url = f"{self._server_url}/repos/{owner}/{repo_name}/contents/{path}"
            params = {"ref": branch}
            response = requests.get(url, headers=self._headers, params=params, timeout=30)

            if response.status_code != 200:
                error_msg = f"GitHub API error: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

            data = response.json()
            # Format output to be more readable/useful
            result = [
                {
                    "name": item["name"],
                    "path": item["path"],
                    "type": item["type"],
                    "size": item.get("size", 0),
                }
                for item in data
            ]
            return json.dumps(result, indent=2)

        except Exception as e:
            error_msg = f"Error listing directory {path}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def get_branch_info(self, repo: str, branch: str) -> str:
        """Get branch information including SHA.

        Args:
            repo: Repository in format "owner/repo"
            branch: Branch name

        Returns:
            JSON string containing branch metadata including SHA
        """
        try:
            logger.info(f"Getting info for branch {branch} in {repo}")

            parts = repo.split("/")
            if len(parts) != 2:
                return json.dumps({"error": "Repository must be in format 'owner/repo'"})

            owner, repo_name = parts

            url = f"{self._server_url}/repos/{owner}/{repo_name}/branches/{branch}"
            response = requests.get(url, headers=self._headers, timeout=30)

            if response.status_code != 200:
                error_msg = f"GitHub API error: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

            data = response.json()
            return json.dumps(
                {
                    "name": data["name"],
                    "sha": data["commit"]["sha"],
                    "protected": data.get("protected", False),
                },
                indent=2,
            )

        except Exception as e:
            error_msg = f"Error getting branch info for {branch}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def create_branch(self, repo: str, base_branch: str, new_branch_name: str) -> str:
        """Create a new branch from a base branch.

        Args:
            repo: Repository in format "owner/repo"
            base_branch: Name of the base branch (e.g., "main")
            new_branch_name: Name of the new branch to create

        Returns:
            JSON string with result status
        """
        try:
            logger.info(f"Creating branch {new_branch_name} from {base_branch} in {repo}")

            parts = repo.split("/")
            if len(parts) != 2:
                return json.dumps({"error": "Repository must be in format 'owner/repo'"})

            owner, repo_name = parts

            # Get SHA of base branch
            base_info_json = self.get_branch_info(repo, base_branch)
            base_info = json.loads(base_info_json)

            if "error" in base_info:
                return base_info_json

            sha = base_info["sha"]

            # Create new branch
            url = f"{self._server_url}/repos/{owner}/{repo_name}/git/refs"
            data = {"ref": f"refs/heads/{new_branch_name}", "sha": sha}
            response = requests.post(url, headers=self._headers, json=data, timeout=30)

            if response.status_code == 201:
                return json.dumps(
                    {"status": "success", "message": f"Branch {new_branch_name} created successfully", "sha": sha}
                )
            else:
                error_msg = f"Failed to create branch: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

        except Exception as e:
            error_msg = f"Error creating branch {new_branch_name}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def create_or_update_file(
        self, repo: str, branch: str, path: str, content: str, message: str, sha: str | None = None
    ) -> str:
        """Create or update a file in the repository.

        Args:
            repo: Repository in format "owner/repo"
            branch: Branch to commit to
            path: File path in repository
            content: New file content (text)
            message: Commit message
            sha: SHA of the file being replaced (required for updates, optional for creation)

        Returns:
            JSON string with commit result
        """
        try:
            logger.info(f"Writing file {path} to {repo} on branch {branch}")

            parts = repo.split("/")
            if len(parts) != 2:
                return json.dumps({"error": "Repository must be in format 'owner/repo'"})

            owner, repo_name = parts

            # If sha not provided, try to get it (might be an update)
            if not sha:
                try:
                    # Check if file exists
                    url_get = f"{self._server_url}/repos/{owner}/{repo_name}/contents/{path}"
                    params = {"ref": branch}
                    resp_get = requests.get(url_get, headers=self._headers, params=params, timeout=10)
                    if resp_get.status_code == 200:
                        sha = resp_get.json()["sha"]
                except Exception:
                    pass  # File probably doesn't exist, proceed with creation

            # Encode content
            encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

            url = f"{self._server_url}/repos/{owner}/{repo_name}/contents/{path}"
            data = {
                "message": message,
                "content": encoded_content,
                "branch": branch,
            }
            if sha:
                data["sha"] = sha

            response = requests.put(url, headers=self._headers, json=data, timeout=30)

            if response.status_code in [200, 201]:
                result = response.json()
                return json.dumps(
                    {
                        "status": "success",
                        "content": result["content"],
                        "commit": result["commit"],
                    }
                )
            else:
                error_msg = f"Failed to write file: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

        except Exception as e:
            error_msg = f"Error writing file {path}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def create_pull_request(
        self, repo: str, head_branch: str, base_branch: str, title: str, body: str
    ) -> str:
        """Create a pull request.

        Args:
            repo: Repository in format "owner/repo"
            head_branch: Name of the branch containing changes (can be "owner:branch" for forks)
            base_branch: Name of the branch to merge into (e.g., "main")
            title: Title of the pull request
            body: Description/body of the pull request

        Returns:
            JSON string with created PR details including number and URL
        """
        try:
            logger.info(f"Creating PR in {repo}: {head_branch} -> {base_branch}")

            parts = repo.split("/")
            if len(parts) != 2:
                return json.dumps({"error": "Repository must be in format 'owner/repo'"})

            owner, repo_name = parts

            url = f"{self._server_url}/repos/{owner}/{repo_name}/pulls"
            data = {
                "title": title,
                "body": body,
                "head": head_branch,
                "base": base_branch,
            }

            response = requests.post(url, headers=self._headers, json=data, timeout=30)

            if response.status_code == 201:
                pr = response.json()
                return json.dumps(
                    {
                        "status": "success",
                        "number": pr["number"],
                        "url": pr["html_url"],
                        "title": pr["title"],
                    }
                )
            else:
                error_msg = f"Failed to create PR: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

        except Exception as e:
            error_msg = f"Error creating PR: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def add_pr_comment(self, repo: str, pr_number: int, comment: str) -> str:
        """Add a comment to a pull request.

        Args:
            repo: Repository in format "owner/repo"
            pr_number: Pull request number
            comment: Comment text

        Returns:
            JSON string with result status
        """
        try:
            logger.info(f"Adding comment to PR #{pr_number} in {repo}")

            parts = repo.split("/")
            if len(parts) != 2:
                return json.dumps({"error": "Repository must be in format 'owner/repo'"})

            owner, repo_name = parts

            url = f"{self._server_url}/repos/{owner}/{repo_name}/issues/{pr_number}/comments"
            data = {"body": comment}

            response = requests.post(url, headers=self._headers, json=data, timeout=30)

            if response.status_code == 201:
                return json.dumps({"status": "success", "message": "Comment added successfully"})
            else:
                error_msg = f"Failed to add comment: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

        except Exception as e:
            error_msg = f"Error adding comment to PR #{pr_number}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def sync_fork(self, repo: str, branch: str = "main") -> str:
        """Sync a fork with its upstream repository.

        Args:
            repo: Repository in format "owner/repo"
            branch: Branch to sync (default: "main")

        Returns:
            JSON string with result status
        """
        try:
            logger.info(f"Syncing fork {repo} branch {branch} with upstream")

            parts = repo.split("/")
            if len(parts) != 2:
                return json.dumps({"error": "Repository must be in format 'owner/repo'"})

            owner, repo_name = parts

            # Use GitHub's merge-upstream endpoint
            url = f"{self._server_url}/repos/{owner}/{repo_name}/merge-upstream"
            data = {"branch": branch}

            response = requests.post(url, headers=self._headers, json=data, timeout=30)

            if response.status_code in [200, 409]:  # 409 conflict means branch is already up to date or conflict
                # Even if 409, check message to distinguish conflict vs up-to-date
                result = response.json()
                return json.dumps(
                    {
                        "status": "success" if response.status_code == 200 else "info",
                        "message": result.get("message", "Sync attempted"),
                    }
                )
            else:
                error_msg = f"Failed to sync fork: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

        except Exception as e:
            error_msg = f"Error syncing fork {repo}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    def create_fork(self, owner: str, repo: str) -> str:
        """Create a fork of a repository.

        Args:
            owner: Owner of the upstream repository
            repo: Name of the upstream repository

        Returns:
            JSON string with created fork details
        """
        try:
            logger.info(f"Creating fork of {owner}/{repo}")

            url = f"{self._server_url}/repos/{owner}/{repo}/forks"
            response = requests.post(url, headers=self._headers, timeout=30)

            if response.status_code == 202:
                fork = response.json()
                return json.dumps(
                    {
                        "status": "success",
                        "message": "Fork creation started",
                        "full_name": fork.get("full_name"),
                        "html_url": fork.get("html_url"),
                    }
                )
            else:
                error_msg = f"Failed to create fork: {response.status_code} {response.text}"
                logger.error(error_msg)
                return json.dumps({"error": error_msg})

        except Exception as e:
            error_msg = f"Error creating fork of {owner}/{repo}: {str(e)}"
            logger.error(error_msg)
            return json.dumps({"error": error_msg})

    # Private helper methods

    def _calculate_pr_score(self, pr: dict, repo: str) -> dict[str, Any]:
        """Calculate priority score for a PR (0-100 scale).

        Scoring algorithm:
        - Age (25%): Days since creation, capped at 7 days
        - Size (20%): Inverse of changes (smaller = higher)
        - Activity (15%): Recent comments/reviews
        - Labels (10%): urgent/hotfix/blocking boost
        - Author (10%): First-time contributor bonus

        Args:
            pr: Pull request data dictionary
            repo: Repository name (for logging)

        Returns:
            Dictionary with total_score, breakdown, and priority_tier
        """
        # Age score (0-25): Days since creation, capped at 7 days
        created_at = pr.get("created_at", "")
        try:
            created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            age_days = (datetime.now(UTC) - created).days
            age_score = min(age_days / 7.0, 1.0) * 25
        except Exception:
            age_score = 0

        # Size score (0-20): Inverse of changes (smaller = better)
        changes = pr.get("additions", 0) + pr.get("deletions", 0)
        if changes == 0:
            size_score = 20
        else:
            size_score = max(0, 20 - (changes / 100))  # Penalize after 100 lines

        # Activity score (0-15): Recent comments/reviews
        comments = pr.get("comments", 0)
        review_comments = pr.get("review_comments", 0)
        activity = comments + review_comments
        activity_score = min(activity / 10.0, 1.0) * 15

        # Label score (0-10): urgent/hotfix/blocking
        labels = [label.get("name", "").lower() for label in pr.get("labels", [])]
        label_score = 0
        if any(keyword in " ".join(labels) for keyword in ["urgent", "hotfix", "blocking", "critical"]):
            label_score = 10
        elif any(keyword in " ".join(labels) for keyword in ["high-priority", "important"]):
            label_score = 7

        # Author score (0-10): Could check if first-time contributor
        # For simplicity, give base score
        author_score = 5

        # Calculate total (max 80 without CI)
        total_score = age_score + size_score + activity_score + label_score + author_score

        # Determine priority tier
        if total_score >= 65:
            priority_tier = "CRITICAL"
        elif total_score >= 50:
            priority_tier = "HIGH"
        elif total_score >= 35:
            priority_tier = "MEDIUM"
        else:
            priority_tier = "LOW"

        return {
            "total_score": round(total_score, 2),
            "breakdown": {
                "age": round(age_score, 2),
                "size": round(size_score, 2),
                "activity": round(activity_score, 2),
                "labels": round(label_score, 2),
                "author": round(author_score, 2),
            },
            "priority_tier": priority_tier,
        }

    def _generate_review_reasoning(self, pr: dict) -> str:
        """Generate human-readable reasoning for why this PR should be reviewed.

        Args:
            pr: Pull request data with score breakdown

        Returns:
            String explaining the priority reasoning
        """
        reasons = []
        breakdown = pr.get("score_breakdown", {})

        # Age reasoning
        age_score = breakdown.get("age", 0)
        if age_score >= 20:
            reasons.append("This PR has been open for a while and needs attention to avoid becoming stale")
        elif age_score >= 10:
            reasons.append("This PR has moderate age")

        # Size reasoning
        size_score = breakdown.get("size", 0)
        if size_score >= 15:
            reasons.append("Small PR that should be quick to review")
        elif size_score >= 10:
            reasons.append("Moderate-sized PR")

        # Activity reasoning
        activity_score = breakdown.get("activity", 0)
        if activity_score >= 10:
            reasons.append("Active discussion suggests this is important")

        # Label reasoning
        label_score = breakdown.get("labels", 0)
        if label_score >= 10:
            reasons.append("⚠️ Marked as urgent/hotfix/blocking - needs immediate attention")
        elif label_score >= 5:
            reasons.append("Marked as high priority")

        if not reasons:
            reasons.append("Standard priority PR ready for review")

        return " • ".join(reasons)
