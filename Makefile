.PHONY: prepare-commit lint format typecheck test validate-tooling

# Main commit preparation - use pre-commit hooks for consistency
prepare-commit:
	@echo "🚀 Preparing commit..."
	git add .
	@echo "🔍 Running pre-commit hooks..."
	pre-commit run --all-files

# Development commands
lint:
	@echo "🔍 Running linter..."
	uv run ruff check --fix

format:
	@echo "🎨 Formatting code..."
	uv run ruff format

typecheck:
	@echo "🏷️  Type checking..."
	uv run mypy src tests --ignore-missing-imports

test:
	@echo "🧪 Running tests..."
	uv run pytest

# Validate tool configuration consistency
validate-tooling:
	@echo "🔍 Validating tooling configuration..."
	@echo "📋 Checking ruff..."
	@uv run ruff check src tests --diff || echo "⚠️  Ruff would make changes"
	@echo "🪝 Checking pre-commit..."
	@pre-commit run --all-files || echo "⚠️  Pre-commit hooks would modify files"
	@echo "✅ Tooling validation complete"

# Run all quality checks
quality: lint typecheck test
	@echo "✅ All quality checks passed"
