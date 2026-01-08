# Complete Bindu Agent Setup Guide: From Zero to Production

**Version:** 1.0  
**Date:** January 8, 2026  
**Framework:** Bindu Agent Framework v2026.1.7  
**Author:** Senior DevOps Engineer

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Project Initialization](#project-initialization)
3. [Project Structure](#project-structure)
4. [Configuration Setup](#configuration-setup)
5. [GitHub Repository Setup](#github-repository-setup)
6. [GitHub Secrets Configuration](#github-secrets-configuration)
7. [GitHub Actions Workflow Setup](#github-actions-workflow-setup)
8. [Local Development](#local-development)
9. [Testing](#testing)
10. [Deployment](#deployment)
11. [Registration on bindu.directory](#registration-on-bindudirectory)
12. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **OS:** Linux, macOS, or Windows (WSL2)
- **Python:** 3.12 or higher
- **Git:** Latest version
- **Docker:** Latest version (for containerization)
- **GitHub CLI:** `gh` command-line tool

### Install Required Tools

```bash
# Install uv (Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install GitHub CLI (Ubuntu/Debian)
sudo apt install gh

# Or macOS
brew install gh

# Authenticate with GitHub
gh auth login

# Install Docker (Ubuntu)
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER

# Verify installations
uv --version
gh --version
docker --version
python3 --version
```

### API Keys Required
Obtain these keys before starting:

1. **OpenRouter API Key** (REQUIRED)
   - URL: https://openrouter.ai/keys
   - Used for: LLM inference (GPT-5)

2. **Mem0 API Key** (REQUIRED)
   - URL: https://app.mem0.ai/dashboard/api-keys
   - Used for: Persistent memory

3. **Bindu API Token** (REQUIRED)
   - URL: https://bindus.directory (after login)
   - Used for: Agent registration

4. **Firecrawl API Key** (OPTIONAL)
   - URL: https://firecrawl.dev/
   - Used for: Web scraping

5. **Docker Hub Token** (OPTIONAL)
   - URL: https://hub.docker.com/settings/security
   - Used for: CI/CD Docker pushes

6. **GitHub Personal Access Token** (OPTIONAL)
   - URL: https://github.com/settings/tokens
   - Scope: `repo`
   - Used for: Repository operations

---

## Project Initialization

### Step 1: Create Project from Template

```bash
# Navigate to your projects directory
cd ~/Documents/Code/Projects

# Create new Bindu agent using cookiecutter
uvx cookiecutter https://github.com/GetBindu/Bindu-Agent-Template

# Answer the prompts:
# - agent_name: web-extraction-agent
# - agent_description: An AI agent that transforms unstructured web content into organized, structured data
# - author_name: Your Name
# - author_email: your.email@example.com
# - github_username: yourusername
# - python_version: 3.12

cd web-extraction-agent
```

### Step 2: Initialize Git Repository

```bash
# Initialize git
git init

# Create GitHub repository
gh repo create web-extraction-agent --public --source=. --remote=origin

# Set default branch to master (if not already)
git branch -M master

# Initial commit
git add .
git commit -m "feat: initial project setup from Bindu Agent Template"
git push -u origin master
```

---

## Project Structure

After initialization, your project structure should look like:

```
web-extraction-agent/
├── .github/
│   ├── workflows/
│   │   ├── main.yml                    # CI/CD for tests
│   │   ├── build-and-push.yml          # Docker build & bindu.directory registration
│   │   ├── on-release-main.yml         # Release automation
│   │   └── validate-codecov-config.yml # Code coverage validation
│   └── actions/
│       └── setup-python-env/           # Reusable setup action
├── web_extraction_agent/
│   ├── __init__.py
│   ├── __main__.py                     # Agent entry point
│   ├── __version__.py                  # Version management
│   ├── main.py                         # Core agent logic
│   ├── agent_config.json               # Bindu configuration
│   ├── config_manager.py               # Dynamic configuration
│   └── tool_manager.py                 # MCP tool management
├── tests/
│   ├── test_main.py                    # Unit tests
│   └── test_integration.py             # Integration tests
├── docs/                               # Documentation
├── .env.example                        # Environment template
├── .env                                # Your secrets (DO NOT COMMIT)
├── .gitignore
├── .pre-commit-config.yaml             # Code quality hooks
├── pyproject.toml                      # Python dependencies
├── uv.lock                             # Locked dependencies
├── Dockerfile.agent                    # Agent container
├── docker-compose.yml                  # Local development
├── Makefile                            # Build automation
└── README.md
```

---

## Configuration Setup

### Step 1: Create Environment File

```bash
# Copy template
cp .env.example .env

# Edit .env with your actual keys
nano .env  # or vim, or your preferred editor
```

### Step 2: Configure .env File

```dotenv
# ============================================
# Environment Variables Configuration
# ============================================

# --------------------------------------------
# OpenRouter API Configuration (REQUIRED)
# --------------------------------------------
OPENROUTER_API_KEY="sk-or-v1-YOUR_KEY_HERE"

# --------------------------------------------
# Mem0 Memory Configuration (REQUIRED)
# --------------------------------------------
MEM0_API_KEY="m0-YOUR_KEY_HERE"

# --------------------------------------------
# Bindu Directory Token (REQUIRED)
# --------------------------------------------
BINDU_API_TOKEN="bindu_sk_YOUR_TOKEN_HERE"

# --------------------------------------------
# Firecrawl API Configuration (OPTIONAL)
# --------------------------------------------
FIRECRAWL_API_KEY="fc-YOUR_KEY_HERE"

# --------------------------------------------
# Docker Hub Token (OPTIONAL)
# --------------------------------------------
DOCKERHUB_TOKEN="dckr_pat_YOUR_TOKEN_HERE"

# --------------------------------------------
# GitHub Access Token (OPTIONAL)
# --------------------------------------------
GH_ACCESS_TOKEN="github_pat_YOUR_TOKEN_HERE"

# --------------------------------------------
# Model Configuration
# --------------------------------------------
MODEL_NAME="openai/gpt-5"

# --------------------------------------------
# Output Directory
# --------------------------------------------
OUTPUT_DIR="./output"
```

### Step 3: Update agent_config.json

Edit `web_extraction_agent/agent_config.json`:

```json
{
  "name": "web-extraction-agent",
  "author": "your.email@example.com",
  "description": "An AI agent that transforms unstructured web content into organized, structured data by combining Firecrawl's web scraping with Pydantic's structured output validation.",
  "version": "1.0.0",
  "agent_trust": "medium",
  "deployment": {
    "url": "0.0.0.0",
    "port": 3773,
    "protocol_version": "2025.49.3"
  },
  "memory": {
    "storage": "in-memory",
    "max_history": 100
  },
  "scheduler": {
    "type": "in-memory",
    "max_workers": 4
  },
  "skills": [],
  "capabilities": {},
  "num_history_sessions": 5,
  "debug_mode": true,
  "debug_level": 2,
  "environment_variables": [
    {
      "name": "OPENROUTER_API_KEY",
      "required": true,
      "description": "OpenRouter API key for LLM access"
    },
    {
      "name": "MEM0_API_KEY",
      "required": true,
      "description": "Mem0 API key for memory storage"
    },
    {
      "name": "FIRECRAWL_API_KEY",
      "required": false,
      "description": "Firecrawl API key for web scraping"
    }
  ],
  "metadata": {
    "domain": "web-scraping",
    "specialization": "data-extraction"
  }
}
```

---

## GitHub Repository Setup

### Step 1: Verify Repository Exists

```bash
# Check current repository
gh repo view

# Expected output:
# name: web-extraction-agent
# owner: yourusername
```

### Step 2: Set Repository Settings

```bash
# Enable GitHub Actions (if not already enabled)
gh api repos/:owner/:repo -X PATCH -f has_issues=true -f has_wiki=true -f has_projects=true

# Set default branch to master
gh api repos/:owner/:repo -X PATCH -f default_branch=master
```

---

## GitHub Secrets Configuration

### Critical: Upload All Secrets to GitHub

GitHub Actions workflows require secrets to be stored in the repository. **Never commit .env to git.**

```bash
# Navigate to your project
cd web-extraction-agent

# Upload each secret using gh CLI
gh secret set OPENROUTER_API_KEY --body "sk-or-v1-YOUR_ACTUAL_KEY"
gh secret set MEM0_API_KEY --body "m0-YOUR_ACTUAL_KEY"
gh secret set BINDU_API_TOKEN --body "bindu_sk_YOUR_ACTUAL_TOKEN"
gh secret set FIRECRAWL_API_KEY --body "fc-YOUR_ACTUAL_KEY"
gh secret set DOCKERHUB_TOKEN --body "dckr_pat_YOUR_ACTUAL_TOKEN"
gh secret set GH_ACCESS_TOKEN --body "github_pat_YOUR_ACTUAL_TOKEN"
gh secret set MODEL_NAME --body "openai/gpt-5"

# Verify all secrets are uploaded
gh secret list

# Expected output:
# NAME                UPDATED
# BINDU_API_TOKEN     less than a minute ago
# DOCKERHUB_TOKEN     less than a minute ago
# FIRECRAWL_API_KEY   less than a minute ago
# GH_ACCESS_TOKEN     less than a minute ago
# MEM0_API_KEY        less than a minute ago
# MODEL_NAME          less than a minute ago
# OPENROUTER_API_KEY  less than a minute ago
```

### Automated Script (Optional)

Create a script to upload secrets automatically:

```bash
#!/bin/bash
# upload_secrets.sh

set -e

echo "🔐 Uploading GitHub Secrets..."

# Source .env file
source .env

# Upload secrets
gh secret set OPENROUTER_API_KEY --body "$OPENROUTER_API_KEY"
gh secret set MEM0_API_KEY --body "$MEM0_API_KEY"
gh secret set BINDU_API_TOKEN --body "$BINDU_API_TOKEN"
gh secret set FIRECRAWL_API_KEY --body "$FIRECRAWL_API_KEY"
gh secret set DOCKERHUB_TOKEN --body "$DOCKERHUB_TOKEN"
gh secret set GH_ACCESS_TOKEN --body "$GH_ACCESS_TOKEN"
gh secret set MODEL_NAME --body "$MODEL_NAME"

echo "✅ All secrets uploaded successfully!"
gh secret list
```

Make it executable and run:

```bash
chmod +x upload_secrets.sh
./upload_secrets.sh
```

---

## GitHub Actions Workflow Setup

### Step 1: Update build-and-push.yml

**Critical Fix:** Ensure the workflow triggers on your branch (master or main).

Edit `.github/workflows/build-and-push.yml`:

```yaml
name: Build and Push to Docker Hub

on:
  push:
    branches:
      - master  # ⚠️ CHANGE THIS TO MATCH YOUR BRANCH
    paths:
      - 'Dockerfile.agent'
      - 'web_extraction_agent/**'
      - 'pyproject.toml'
      - 'uv.lock'
      - '.version'
      - '.github/workflows/build-and-push.yml'
  workflow_dispatch:  # Allows manual trigger

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: false

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to Docker Hub
        uses: docker/login-action@v3
        with:
          username: yourdockerhubusername  # ⚠️ CHANGE THIS
          password: ${{ secrets.DOCKERHUB_TOKEN }}

      - name: Build and push
        id: docker_build
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile.agent
          push: true
          platforms: linux/amd64,linux/arm64
          tags: yourdockerhubusername/web-extraction-agent:latest  # ⚠️ CHANGE THIS
          cache-from: type=registry,ref=yourdockerhubusername/web-extraction-agent:buildcache
          cache-to: type=registry,ref=yourdockerhubusername/web-extraction-agent:buildcache,mode=max

      - name: Read agent config
        id: agent_config
        run: |
          echo "config=$(cat web_extraction_agent/agent_config.json | jq -c .)" >> $GITHUB_OUTPUT
          echo "version=$(cat .version | tr -d '\n')" >> $GITHUB_OUTPUT

          # Read all skills from the skills folder
          skills_array="[]"
          for skill_dir in web_extraction_agent/skills/*/; do
            if [ -f "${skill_dir}skill.yaml" ]; then
              skill_json=$(cat "${skill_dir}skill.yaml" | yq -o=json -c .)
              skills_array=$(echo "$skills_array" | jq --argjson skill "$skill_json" '. += [$skill]')
            fi
          done
          echo "skills=$(echo $skills_array | jq -c .)" >> $GITHUB_OUTPUT

      - name: Log to backend service
        run: |
          curl --location 'https://bindus.getbindu.com/bindu-register' \
            --header 'accept: application/json' \
            --header 'X-Bindu-CI: true' \
            --header 'X-API-Token: ${{ secrets.BINDU_API_TOKEN }}' \
            --header 'Content-Type: application/json' \
            --data-raw '{
              "agent": {
                "name": "${{ fromJson(steps.agent_config.outputs.config).name }}",
                "author": "${{ fromJson(steps.agent_config.outputs.config).author }}",
                "description": "${{ fromJson(steps.agent_config.outputs.config).description }}",
                "version": "${{ steps.agent_config.outputs.version }}",
                "agent_trust": "${{ fromJson(steps.agent_config.outputs.config).agent_trust }}",
                "type": "research"
              },
              "skills": ${{ toJson(fromJson(steps.agent_config.outputs.skills)) }},
              "framework": {
                "name": "agno",
                "version": "1.0.0"
              },
              "environment_variables": ${{ toJson(fromJson(steps.agent_config.outputs.config).environment_variables) }},
              "execution_cost": ${{ toJson(fromJson(steps.agent_config.outputs.config).execution_cost || fromJson('{}')) }},
              "auth": ${{ toJson(fromJson(steps.agent_config.outputs.config).auth || fromJson('{}')) }},
              "deployment": {
                "url": "${{ fromJson(steps.agent_config.outputs.config).deployment.url }}",
                "protocol_version": "${{ fromJson(steps.agent_config.outputs.config).deployment.protocol_version }}",
                "docker_image": "yourdockerhubusername/web-extraction-agent:latest",
                "docker_digest": "${{ steps.docker_build.outputs.digest }}",
                "platforms": ["linux/amd64", "linux/arm64"]
              },
              "repository": {
                "url": "https://github.com/${{ github.repository }}",
                "commit_sha": "${{ github.sha }}",
                "build_number": "${{ github.run_number }}"
              },
              "metadata": {
                "documentation_url": "https://yourusername.github.io/web-extraction-agent/",
                "domain": "${{ fromJson(steps.agent_config.outputs.config).metadata.domain || 'general' }}",
                "specialization": "${{ fromJson(steps.agent_config.outputs.config).metadata.specialization || 'multi-purpose' }}",
                "last_updated": "${{ github.event.head_commit.timestamp }}"
              }
            }'
```

### Step 2: Commit Workflow Changes

```bash
git add .github/workflows/build-and-push.yml
git commit -m "fix: update workflow to trigger on master branch with correct Docker Hub username"
git push origin master
```

---

## Local Development

### Step 1: Install Dependencies

```bash
# Create virtual environment and install dependencies
uv venv --python 3.12
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies
uv sync

# Install development tools
uv pip install pre-commit
pre-commit install
```

### Step 2: Run Agent Locally

```bash
# Method 1: Using uv
uv run python -m web_extraction_agent

# Method 2: Using docker-compose
docker-compose up

# Method 3: Direct Python
python -m web_extraction_agent
```

### Step 3: Verify Agent is Running

```bash
# Check agent manifest
curl http://localhost:3773/.well-known/agent.json

# Expected response:
# {
#   "id": "...",
#   "name": "web-extraction-agent",
#   "version": "1.0.0",
#   ...
# }
```

---

## Testing

### Step 1: Run All Tests Locally

```bash
# Run pre-commit checks (includes all linters and tests)
make check

# Or run tests individually
uv run pytest tests/ -v

# Run only unit tests
uv run pytest tests/test_main.py -v

# Run integration tests (requires agent to be running)
uv run pytest tests/test_integration.py -v -m integration
```

### Step 2: Test Agent Functionality

```bash
# Send a test message to agent
python3 << 'PYEOF'
import json
import urllib.request
import uuid

msg_id = str(uuid.uuid4())
context_id = str(uuid.uuid4())
task_id = str(uuid.uuid4())
request_id = str(uuid.uuid4())

request = {
    "jsonrpc": "2.0",
    "id": request_id,
    "method": "message/send",
    "params": {
        "configuration": {"acceptedOutputModes": ["text"]},
        "message": {
            "messageId": msg_id,
            "contextId": context_id,
            "taskId": task_id,
            "kind": "message",
            "role": "user",
            "parts": [{"kind": "text", "text": "Extract content from https://example.com"}]
        }
    }
}

data = json.dumps(request).encode('utf-8')
req = urllib.request.Request('http://localhost:3773/', data=data, headers={'Content-Type': 'application/json'})

with urllib.request.urlopen(req, timeout=10) as response:
    result = json.loads(response.read().decode())
    print(json.dumps(result, indent=2))
PYEOF
```

### Step 3: Continuous Testing

```bash
# Watch for file changes and re-run tests
uv run pytest-watch tests/ -v
```

---

## Deployment

### Step 1: Trigger Deployment

```bash
# Option 1: Push to master branch (automatic)
git add .
git commit -m "feat: add new feature"
git push origin master

# Option 2: Manual trigger
gh workflow run build-and-push.yml

# Option 3: Create a release (triggers on-release workflow)
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Step 2: Monitor Deployment

```bash
# List recent workflow runs
gh run list --limit 5

# Watch specific run
gh run view <RUN_ID>

# Download logs
gh run download <RUN_ID>

# Check workflow status
gh run watch
```

### Step 3: Verify Docker Image

```bash
# Pull the image
docker pull yourdockerhubusername/web-extraction-agent:latest

# Run locally
docker run -p 3773:3773 \
  -e OPENROUTER_API_KEY="your_key" \
  -e MEM0_API_KEY="your_key" \
  yourdockerhubusername/web-extraction-agent:latest

# Verify it's working
curl http://localhost:3773/.well-known/agent.json
```

---

## Registration on bindu.directory

### Automatic Registration (Recommended)

When the `build-and-push.yml` workflow completes successfully, your agent is **automatically registered** on bindu.directory.

### Verify Registration

1. Visit: https://bindus.directory
2. Search for: "web-extraction-agent"
3. Check the agent details page

### Manual Registration (Alternative)

If automatic registration fails, use the manual script:

```bash
# Run registration script
uv run python register_on_bindu_directory.py --auto-token

# Or with explicit token
uv run python register_on_bindu_directory.py --token "bindu_sk_YOUR_TOKEN"
```

### Troubleshooting Registration

```bash
# Check if workflow ran successfully
gh run list --workflow=build-and-push.yml --limit 1

# View workflow logs
gh run view <RUN_ID> --log

# Check for registration errors
gh run view <RUN_ID> --log | grep -A 10 "Log to backend service"

# Verify BINDU_API_TOKEN secret exists
gh secret list | grep BINDU_API_TOKEN
```

---

## Troubleshooting

### Common Issues

#### 1. Workflow Not Triggering

**Symptom:** Push to master doesn't trigger build-and-push workflow

**Solution:**
```bash
# Check current branch
git branch --show-current

# If on 'main', update workflow:
# Edit .github/workflows/build-and-push.yml
# Change: branches: [main]
# To: branches: [master]

# Or rename branch to main:
git branch -M main
git push -u origin main
```

#### 2. Missing Secrets

**Symptom:** Workflow fails with "secret not found"

**Solution:**
```bash
# List all secrets
gh secret list

# Re-upload missing secret
gh secret set SECRET_NAME --body "secret_value"
```

#### 3. Docker Build Fails

**Symptom:** Docker build step fails in workflow

**Solution:**
```bash
# Test build locally
docker build -f Dockerfile.agent -t test-agent .

# Check Dockerfile for errors
cat Dockerfile.agent

# Verify all dependencies in pyproject.toml
cat pyproject.toml
```

#### 4. Integration Tests Fail

**Symptom:** Tests pass locally but fail in CI

**Solution:**
```bash
# Integration tests need environment variables
# They automatically skip if vars are missing

# Check test logs
gh run view <RUN_ID> --log | grep -A 20 "pytest"

# Ensure integration tests use pytest.skip properly
```

#### 5. Agent Not Appearing on bindu.directory

**Symptom:** Workflow succeeds but agent not listed

**Solution:**
```bash
# Check registration step logs
gh run view <RUN_ID> --log | grep -A 30 "Log to backend service"

# Verify BINDU_API_TOKEN is valid
# Login to https://bindus.directory and regenerate token

# Re-upload token
gh secret set BINDU_API_TOKEN --body "new_token"

# Trigger workflow again
gh workflow run build-and-push.yml
```

#### 6. Port Already in Use

**Symptom:** "Address already in use: 3773"

**Solution:**
```bash
# Find process using port 3773
lsof -i :3773
# Or
netstat -tulpn | grep 3773

# Kill the process
kill -9 <PID>

# Or use a different port in agent_config.json
```

---

## Best Practices

### Security
- ✅ Never commit `.env` to git
- ✅ Use GitHub Secrets for all sensitive data
- ✅ Rotate API keys regularly
- ✅ Use least-privilege access tokens
- ✅ Enable 2FA on all accounts

### Development
- ✅ Run `make check` before every commit
- ✅ Use pre-commit hooks for code quality
- ✅ Write tests for new features
- ✅ Keep dependencies updated
- ✅ Document all configuration changes

### CI/CD
- ✅ Test locally before pushing
- ✅ Monitor workflow runs
- ✅ Use semantic versioning (v1.0.0, v1.1.0, etc.)
- ✅ Tag releases properly
- ✅ Keep Docker images lean

### Debugging
- ✅ Check workflow logs first
- ✅ Verify all secrets are set
- ✅ Test Docker builds locally
- ✅ Use `gh run watch` for real-time monitoring
- ✅ Enable debug mode in agent_config.json for development

---

## Quick Reference

### Essential Commands

```bash
# Setup
uv venv --python 3.12 && source .venv/bin/activate
uv sync
pre-commit install

# Development
uv run python -m web_extraction_agent
make check

# Testing
uv run pytest tests/ -v
uv run pytest tests/test_integration.py -v -m integration

# GitHub Operations
gh secret list
gh secret set SECRET_NAME --body "value"
gh run list --limit 5
gh run watch
gh workflow run build-and-push.yml

# Docker
docker-compose up
docker build -f Dockerfile.agent -t web-extraction-agent .
docker run -p 3773:3773 web-extraction-agent

# Git
git add .
git commit -m "feat: description"
git push origin master
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0
```

### Important URLs
- **bindu.directory:** https://bindus.directory
- **Bindu Framework:** https://github.com/GetBindu/Bindu
- **Bindu Docs:** https://docs.getbindu.com
- **OpenRouter:** https://openrouter.ai
- **Mem0:** https://app.mem0.ai
- **Firecrawl:** https://firecrawl.dev

---

## Summary Checklist

Use this checklist to ensure everything is set up correctly:

### Initial Setup
- [ ] Installed uv, gh CLI, Docker
- [ ] Obtained all required API keys
- [ ] Created project with cookiecutter
- [ ] Initialized git repository
- [ ] Created GitHub repository

### Configuration
- [ ] Created and configured .env file
- [ ] Updated agent_config.json
- [ ] Added .env to .gitignore
- [ ] Verified .env.example is up to date

### GitHub Setup
- [ ] Uploaded all secrets to GitHub
- [ ] Verified secrets with `gh secret list`
- [ ] Updated workflow branch trigger (main/master)
- [ ] Updated Docker Hub username in workflow
- [ ] Updated documentation URLs in workflow

### Development
- [ ] Installed dependencies with `uv sync`
- [ ] Installed pre-commit hooks
- [ ] Tested agent locally
- [ ] All tests pass with `make check`
- [ ] Agent responds at http://localhost:3773

### Deployment
- [ ] Pushed code to GitHub
- [ ] Workflow triggered successfully
- [ ] Docker image built and pushed
- [ ] Agent registered on bindu.directory
- [ ] Verified agent appears on directory

### Final Verification
- [ ] Agent accessible via Docker image
- [ ] All environment variables working
- [ ] Integration tests pass in CI
- [ ] Documentation is complete
- [ ] README is updated

---

## Conclusion

This guide covers the complete lifecycle of a Bindu agent from initialization to production deployment. By following these steps, you should have:

1. ✅ A fully functional Bindu agent
2. ✅ Automated CI/CD pipeline
3. ✅ Docker containerization
4. ✅ Registration on bindu.directory
5. ✅ Comprehensive testing
6. ✅ Production-ready deployment

For additional help:
- GitHub Issues: https://github.com/GetBindu/Bindu/issues
- Documentation: https://docs.getbindu.com
- Community: https://discord.gg/bindu

**Happy Building! 🚀**
