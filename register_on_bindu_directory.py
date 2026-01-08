"""Script to register the web-extraction-agent on bindu.directory.

This script registers the agent with the Bindu Directory, making it discoverable
and available for use by other agents and applications.

Usage:
    # Get token and register in one command
    uv run python register_on_bindu_directory.py --auto-token

    # Or use existing token
    uv run python register_on_bindu_directory.py --token "your_token_here"
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.table import Table

# Load environment variables
load_dotenv()

console = Console()

# Bindu Directory API endpoint
BINDU_DIRECTORY_API = "https://api.bindu.directory"
BINDU_DIRECTORY_WEB = "https://bindu.directory"

# Agent configuration
AGENT_CONFIG_FILE = Path(__file__).parent / "web_extraction_agent" / "agent_config.json"


def load_agent_config() -> dict:
    """Load the agent configuration."""
    if not AGENT_CONFIG_FILE.exists():
        console.print(f"[red]Error:[/red] Agent config not found at {AGENT_CONFIG_FILE}")
        sys.exit(1)

    with open(AGENT_CONFIG_FILE) as f:
        return json.load(f)


def get_auth0_token(domain: str, client_id: str, client_secret: str) -> str:
    """Get Auth0 access token using client credentials flow."""
    audience = f"https://{domain}/api/v2/"
    url = f"https://{domain}/oauth/token"

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "audience": audience,
        "grant_type": "client_credentials",
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()["access_token"]
    except requests.exceptions.HTTPError as e:
        console.print(f"[red]HTTP Error {e.response.status_code}:[/red] {e.response.text}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error obtaining token:[/red] {e}")
        sys.exit(1)


def register_agent(agent_config: dict, token: str) -> bool:
    """Register the agent on bindu.directory.

    Args:
        agent_config: The agent configuration dictionary
        token: Authentication token for the directory API

    Returns:
        True if registration was successful, False otherwise
    """
    # Prepare registration payload
    payload = {
        "name": agent_config.get("name"),
        "description": agent_config.get("description"),
        "author": agent_config.get("author"),
        "version": agent_config.get("version", "1.0.0"),
        "repository_url": os.getenv("GITHUB_REPOSITORY_URL", ""),
        "documentation_url": os.getenv("DOCUMENTATION_URL", ""),
        "capabilities": agent_config.get("capabilities", {}),
        "skills": agent_config.get("skills", []),
        "deployment": agent_config.get("deployment", {}),
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        with Progress() as progress:
            task = progress.add_task("[cyan]Registering agent on bindu.directory...", total=None)

            response = requests.post(
                f"{BINDU_DIRECTORY_API}/agents/register",
                json=payload,
                headers=headers,
                timeout=30,
            )

            progress.stop_task(task)

        if response.status_code == 201:
            result = response.json()
            console.print(
                Panel(
                    f"[green]✓ Agent successfully registered![/green]\n\n"
                    f"Agent ID: {result.get('id')}\n"
                    f"View at: {BINDU_DIRECTORY_WEB}/agents/{result.get('id')}",
                    title="[bold green]Registration Success[/bold green]",
                    border_style="green",
                )
            )
            return True
        elif response.status_code == 409:
            # Agent already exists
            console.print(
                Panel(
                    "[yellow]⚠ Agent already registered on bindu.directory[/yellow]\n\n"
                    "The agent may already exist. You can update it with the --update flag.",
                    title="[bold yellow]Agent Exists[/bold yellow]",
                    border_style="yellow",
                )
            )
            return True
        else:
            console.print(f"[red]Registration failed:[/red] Status {response.status_code}\n{response.text}")
            return False

    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error during registration:[/red] {e}")
        return False


def display_agent_info(agent_config: dict) -> None:
    """Display agent information in a formatted table."""
    table = Table(title="Agent Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="magenta")

    table.add_row("Name", agent_config.get("name", "N/A"))
    table.add_row("Author", agent_config.get("author", "N/A"))
    table.add_row("Version", agent_config.get("version", "1.0.0"))
    table.add_row("Description", agent_config.get("description", "N/A")[:60] + "...")

    console.print(table)


def main():
    """Execute the registration flow for bindu.directory."""
    parser = argparse.ArgumentParser(
        description="Register web-extraction-agent on bindu.directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Register with automatic token fetch
  uv run python register_on_bindu_directory.py --auto-token

  # Register with provided token
  uv run python register_on_bindu_directory.py --token "your_token"

  # Use environment variables (set BINDU_API_TOKEN, AUTH0_DOMAIN, etc.)
  uv run python register_on_bindu_directory.py --auto-token
        """,
    )

    parser.add_argument(
        "--token",
        help="Bindu Directory API token for authentication",
        default=os.getenv("BINDU_API_TOKEN"),
    )
    parser.add_argument(
        "--auto-token",
        action="store_true",
        help="Automatically fetch token from Auth0 (requires Auth0 credentials)",
    )
    parser.add_argument(
        "--auth0-domain",
        default=os.getenv("AUTH0_DOMAIN"),
        help="Auth0 domain for token generation",
    )
    parser.add_argument(
        "--auth0-client-id",
        default=os.getenv("AUTH0_CLIENT_ID"),
        help="Auth0 client ID for token generation",
    )
    parser.add_argument(
        "--auth0-client-secret",
        default=os.getenv("AUTH0_CLIENT_SECRET"),
        help="Auth0 client secret for token generation",
    )
    parser.add_argument(
        "--skip-verification",
        action="store_true",
        help="Skip SSL verification (not recommended for production)",
    )

    args = parser.parse_args()

    # Display banner
    console.print(
        Panel(
            "[bold cyan]🚀 Bindu Directory Agent Registration[/bold cyan]\n"
            "[dim]Registering web-extraction-agent on bindu.directory[/dim]",
            border_style="cyan",
        )
    )

    # Load agent config
    console.print("\n[cyan]📋 Loading agent configuration...[/cyan]")
    agent_config = load_agent_config()
    display_agent_info(agent_config)

    # Get token
    token = args.token
    if not token and args.auto_token:
        if not all([args.auth0_domain, args.auth0_client_id, args.auth0_client_secret]):
            console.print(
                "[red]Error:[/red] Missing Auth0 credentials for token generation.\n"
                "Please provide: --auth0-domain, --auth0-client-id, --auth0-client-secret"
            )
            sys.exit(1)

        console.print("\n[cyan]🔐 Fetching authentication token from Auth0...[/cyan]")
        token = get_auth0_token(args.auth0_domain, args.auth0_client_id, args.auth0_client_secret)
        console.print("[green]✓ Token obtained[/green]")

    if not token:
        console.print(
            "[red]Error:[/red] No authentication token provided.\n"
            "Please provide --token or use --auto-token with Auth0 credentials."
        )
        sys.exit(1)

    # Register agent
    console.print("\n[cyan]📤 Registering agent...[/cyan]")
    if register_agent(agent_config, token):
        console.print(
            f"\n[green]✓ Registration complete![/green]\nView your agent at: [cyan]{BINDU_DIRECTORY_WEB}[/cyan]"
        )
        sys.exit(0)
    else:
        console.print("\n[red]✗ Registration failed. Please check the errors above.[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
