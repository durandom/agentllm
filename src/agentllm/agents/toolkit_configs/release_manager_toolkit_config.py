"""
Release Manager toolkit configuration.

Handles downloading and parsing the Excel workbook from Google Drive,
caching the parsed sheets data per user.
"""

import csv
import os
import re
from pathlib import Path

from loguru import logger

from agentllm.agents.base import BaseToolkitConfig
from agentllm.agents.toolkit_configs.gdrive_service_account_config import GDriveServiceAccountConfig
from agentllm.tools.release_manager_toolkit import ReleaseManagerToolkit

# Required sheets in the workbook
REQUIRED_SHEETS = [
    "Configuration & Setup",
    "Tools Reference",
    "Jira Queries",
    "Actions & Workflows",
    "Slack Templates",
    "Maintenance Guide",
    "Prompts",
]

# Required configuration keys in Configuration & Setup sheet
REQUIRED_CONFIG_KEYS = [
    "jira_default_base_jql",
]


class ReleaseManagerToolkitConfig(BaseToolkitConfig):
    """Configuration for Release Manager toolkit.

    Manages downloading the Excel workbook from Google Drive and parsing
    it into in-memory sheet data. Uses a Google Cloud service account for
    authentication (no per-user OAuth required).

    Note: This toolkit does not require user configuration - it automatically
    downloads the workbook when the service account is configured.
    """

    def __init__(self, gdrive_config: GDriveServiceAccountConfig, local_sheets_dir: str | None = None, **kwargs):
        """Initialize Release Manager toolkit config.

        Args:
            gdrive_config: GDrive service account config instance for authentication.
            local_sheets_dir: Local directory path containing CSV sheets.
                             If provided, takes precedence over Google Drive.
                             Useful for testing without service account credentials.
            **kwargs: Additional arguments passed to parent BaseToolkitConfig.

        """
        super().__init__(**kwargs)
        self._gdrive_config = gdrive_config
        self._local_sheets_dir = local_sheets_dir
        self._sheets_cache: dict[str, dict[str, list[dict[str, str]]]] = {}  # {user_id: sheets_data}
        self._workbook_url = os.getenv("RELEASE_MANAGER_WORKBOOK_GDRIVE_URL")

        if not self._local_sheets_dir and not self._workbook_url:
            logger.warning(
                "RELEASE_MANAGER_WORKBOOK_GDRIVE_URL is not set. "
                "Release Manager will not be fully configured until the env var is set "
                "or local_sheets_dir is provided."
            )

    def is_required(self) -> bool:
        """Release Manager toolkit is required.

        Returns:
            True - this toolkit is always required.
        """
        return True

    def extract_and_store_config(self, message: str, user_id: str) -> str | None:
        """Release Manager toolkit does not require user configuration.

        Args:
            message: User message (ignored).
            user_id: User identifier (ignored).

        Returns:
            None - no configuration extraction needed.
        """
        del message, user_id  # Unused parameters required by interface
        return None

    def get_config_prompt(self, user_id: str) -> str | None:
        """Get configuration prompt if required config keys are missing.

        Args:
            user_id: User identifier.

        Returns:
            Configuration prompt if workbook is accessible but missing required keys,
            None otherwise (e.g., if GDrive not configured yet).
        """
        # Check if workbook is accessible (but not necessarily configured)
        workbook_accessible = False
        if self._local_sheets_dir:
            workbook_accessible = True
        elif self._workbook_url and self._gdrive_config.is_configured(user_id):
            workbook_accessible = True

        if not workbook_accessible:
            return None  # GDrive config will handle prompting

        # Check for missing required config keys
        missing_keys = self._get_missing_config_keys(user_id)

        if missing_keys:
            return (
                f"⚠️ Release Manager workbook is missing required configuration:\n\n"
                f"Missing config keys: {', '.join(missing_keys)}\n\n"
                f"Please add these to the 'Configuration & Setup' sheet in your workbook:\n"
                f"Workbook URL: {self._workbook_url or 'local sheets directory'}\n\n"
                f"Required format:\n"
                f"| config_key | value | description |\n"
                f"Example:\n"
                f"| jira_default_base_jql | project IN (RHIDP, RHDHBugs) AND status != closed | Default JQL scope |"
            )

        return None

    def check_authorization_request(self, message: str, user_id: str) -> str | None:
        """Release Manager toolkit does not require authorization requests.

        Args:
            message: User message (ignored).
            user_id: User identifier (ignored).

        Returns:
            None - no authorization prompt needed.
        """
        del message, user_id  # Unused parameters required by interface
        return None

    def is_configured(self, user_id: str) -> bool:
        """Check if Release Manager toolkit is configured for user.

        Returns True if the workbook is accessible (local or via GDrive).
        Does NOT download the workbook — that happens lazily in get_toolkit().
        This avoids masking download errors as "not configured".

        Args:
            user_id: User identifier.

        Returns:
            True if infrastructure is in place, False otherwise.
        """
        if self._local_sheets_dir:
            return True
        if self._workbook_url and self._gdrive_config.is_configured(user_id):
            return True
        return False

    def _get_missing_config_keys(self, user_id: str) -> list[str]:
        """Get list of missing required config keys.

        Args:
            user_id: User identifier.

        Returns:
            List of missing config key names (empty if all present).
        """
        try:
            toolkit = self.get_toolkit(user_id)
            config_values = toolkit.get_all_config_values()
            return [key for key in REQUIRED_CONFIG_KEYS if key not in config_values or not config_values[key]]
        except Exception as e:
            logger.debug(f"Could not check config keys: {e}")
            # If we can't load the toolkit, assume all keys are missing
            return REQUIRED_CONFIG_KEYS.copy()

    def get_toolkit(self, user_id: str) -> ReleaseManagerToolkit:
        """Get or create Release Manager toolkit with cached sheets data.

        Downloads and parses workbook on first access, then caches per user.

        Args:
            user_id: User identifier.

        Returns:
            ReleaseManagerToolkit instance with parsed sheets data.

        Raises:
            RuntimeError: If workbook download or parsing fails.
        """
        # Return cached toolkit if available
        if user_id in self._sheets_cache:
            logger.debug(f"Using cached Release Manager workbook data for user {user_id}")
            return ReleaseManagerToolkit(self._sheets_cache[user_id])

        # Load sheets data from Google Drive
        logger.info(f"Loading Release Manager workbook for user {user_id}")
        sheets_data = self._load_sheets_data(user_id)

        # Cache the sheets data
        self._sheets_cache[user_id] = sheets_data
        logger.success(f"Cached Release Manager workbook data for user {user_id}")

        return ReleaseManagerToolkit(sheets_data)

    def _load_from_local_csvs(self, user_id: str) -> dict[str, list[dict[str, str]]]:
        """Load workbook sheets from local CSV files.

        Reads CSV files from the local sheets directory. File names should match
        the sheet names (with .csv extension).

        Args:
            user_id: User identifier (for logging).

        Returns:
            Dictionary mapping sheet names to list of row dicts.

        Raises:
            RuntimeError: If local directory doesn't exist or sheets can't be loaded.
        """
        if not self._local_sheets_dir:
            raise ValueError("Local sheets directory not configured")

        sheets_dir = Path(self._local_sheets_dir)

        if not sheets_dir.exists():
            raise RuntimeError(
                f"Local sheets directory not found: {sheets_dir}\n"
                f"Please ensure the directory exists with CSV files for all required sheets."
            )

        if not sheets_dir.is_dir():
            raise RuntimeError(f"Local sheets path is not a directory: {sheets_dir}")

        logger.info(f"Loading Release Manager workbook from local CSV files: {sheets_dir}")

        sheets_data: dict[str, list[dict[str, str]]] = {}

        # Load each required sheet
        for sheet_name in REQUIRED_SHEETS:
            # Try exact sheet name first, then sanitized (Google Drive exports & as _)
            sanitized_name = sheet_name.replace("&", "_")
            csv_file = sheets_dir / f"{sheet_name}.csv"

            if not csv_file.exists():
                csv_file = sheets_dir / f"{sanitized_name}.csv"

            if not csv_file.exists():
                raise RuntimeError(
                    f"Required CSV file not found for sheet '{sheet_name}'\n"
                    f"Tried: {sheet_name}.csv and {sanitized_name}.csv\n"
                    f"Expected files for all required sheets: {REQUIRED_SHEETS}"
                )

            try:
                with csv_file.open("r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
                    sheets_data[sheet_name] = rows
                    logger.debug(f"Loaded {len(rows)} rows from {csv_file.name}")

            except Exception as e:
                raise RuntimeError(f"Failed to read CSV file {csv_file}: {e}") from e

        # Validate sheets
        self._validate_sheets(sheets_data)

        logger.success(f"Successfully loaded {len(sheets_data)} sheet(s) from local CSV files for user {user_id}")
        return sheets_data

    def _load_sheets_data(self, user_id: str) -> dict[str, list[dict[str, str]]]:
        """Load workbook sheets from local CSV files or Google Drive.

        Priority:
        1. Local sheets directory (if provided) - no OAuth needed
        2. Google Drive download (requires OAuth)

        Args:
            user_id: User identifier.

        Returns:
            Dictionary mapping sheet names to list of row dicts.

        Raises:
            RuntimeError: If loading fails.
        """
        # Option 1: Load from local CSV files (takes precedence)
        if self._local_sheets_dir:
            return self._load_from_local_csvs(user_id)

        # Option 2: Download from Google Drive
        try:
            # Validate workbook URL is set
            if not self._workbook_url:
                raise ValueError("RELEASE_MANAGER_WORKBOOK_GDRIVE_URL is not set")

            # Extract file_id from Google Sheets URL
            file_id = self._extract_file_id(self._workbook_url)
            logger.debug(f"Extracted file_id: {file_id}")

            # Get GoogleDrive toolkit to access exporter
            gdrive_toolkit = self._gdrive_config.get_toolkit(user_id)
            if gdrive_toolkit is None:
                raise RuntimeError("GoogleDrive toolkit is not available")
            exporter = gdrive_toolkit.exporter

            # Download all sheets as dict
            logger.info(f"Downloading workbook from Google Drive: {file_id}")
            sheets_data = exporter.export_all_sheets_as_dict(file_id)

            # Validate required sheets exist
            self._validate_sheets(sheets_data)

            logger.success(f"Successfully loaded {len(sheets_data)} sheet(s) from workbook")
            return sheets_data

        except Exception as e:
            logger.error(f"Failed to load Release Manager workbook: {e}")
            raise RuntimeError(
                f"Failed to load Release Manager workbook: {e}\n"
                f"Please check:\n"
                f"  1. RELEASE_MANAGER_WORKBOOK_GDRIVE_URL is correct\n"
                f"  2. The workbook is shared with your Google account\n"
                f"  3. You have completed Google Drive OAuth authorization"
            ) from e

    def _extract_file_id(self, url: str) -> str:
        """Extract Google Drive file ID from URL.

        Args:
            url: Google Sheets URL.

        Returns:
            Extracted file ID.

        Raises:
            ValueError: If file_id cannot be extracted from URL.
        """
        # Pattern: /d/FILE_ID/ or ?id=FILE_ID
        pattern = r"/d/([a-zA-Z0-9-_]+)"
        match = re.search(pattern, url)

        if match:
            return match.group(1)

        raise ValueError(f"Could not extract file_id from URL: {url}\nExpected format: https://docs.google.com/spreadsheets/d/FILE_ID/edit")

    def _validate_sheets(self, sheets_data: dict[str, list[dict[str, str]]]) -> None:
        """Validate that all required sheets are present in the workbook.

        Args:
            sheets_data: Dictionary mapping sheet names to row data.

        Raises:
            RuntimeError: If any required sheets are missing.
        """
        missing_sheets = [sheet for sheet in REQUIRED_SHEETS if sheet not in sheets_data]

        if missing_sheets:
            available_sheets = list(sheets_data.keys())
            raise RuntimeError(
                f"Missing required sheets in workbook: {missing_sheets}\n"
                f"Available sheets: {available_sheets}\n"
                f"Required sheets: {REQUIRED_SHEETS}"
            )

        logger.debug(f"Validated all {len(REQUIRED_SHEETS)} required sheets present")
