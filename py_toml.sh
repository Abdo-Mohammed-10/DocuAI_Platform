cat > pyproject.toml << 'EOF'
[project]
name = "DocuAI"
version = "0.1.0"
description = "AI-powered Document Intelligence Platform"
requires-python = ">=3.11"

[tool.ruff]
line-length = 88
select = ["E", "F", "I"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
EOF