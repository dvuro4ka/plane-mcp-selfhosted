"""
Custom MCP server for self-hosted Plane.
Adapts API paths for older self-hosted versions where:
- /api/v1/ works for: projects, issues, states, labels, members, cycles, modules
- /api/ (no v1) works for: pages, users/me (requires session cookie)
- "issues" endpoint is used instead of "work-items"
"""

import json
import os
import sys
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

# --- Configuration ---

BASE_URL = os.getenv("PLANE_BASE_URL", "https://plane.akfixdev.ru").rstrip("/")
API_KEY = os.getenv("PLANE_API_KEY", "")
WORKSPACE = os.getenv("PLANE_WORKSPACE_SLUG", "it")
SESSION_COOKIE = os.getenv("PLANE_SESSION_COOKIE", "")
CSRF_TOKEN = os.getenv("PLANE_CSRF_TOKEN", "")
MCP_HOST = os.getenv("MCP_PUBLIC_HOST", "plane-mcp.akfixdev.ru")

mcp = FastMCP(
    "Plane Self-Hosted",
    instructions="MCP server for self-hosted Plane instance",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=[MCP_HOST, "localhost:*", "127.0.0.1:*"],
    ),
)


# --- HTTP helpers ---

def api_v1_headers() -> dict[str, str]:
    return {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
    }


def session_headers() -> dict[str, str]:
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if SESSION_COOKIE:
        cookie = f"session-id={SESSION_COOKIE}"
        if CSRF_TOKEN:
            cookie += f"; csrftoken={CSRF_TOKEN}"
            headers["X-CSRFToken"] = CSRF_TOKEN
        headers["Cookie"] = cookie
    return headers


def api_v1(path: str) -> str:
    """Build /api/v1/ URL."""
    return f"{BASE_URL}/api/v1/workspaces/{WORKSPACE}/{path.lstrip('/')}"


def api_internal(path: str) -> str:
    """Build /api/ URL (internal, requires session cookie)."""
    return f"{BASE_URL}/api/workspaces/{WORKSPACE}/{path.lstrip('/')}"


def get(url: str, headers: dict, params: dict | None = None) -> Any:
    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=headers, params=params)
        r.raise_for_status()
        return r.json() if r.content else None


def post(url: str, headers: dict, data: dict | None = None) -> Any:
    with httpx.Client(timeout=30) as client:
        r = client.post(url, headers=headers, json=data)
        r.raise_for_status()
        return r.json() if r.content else None


def patch(url: str, headers: dict, data: dict | None = None) -> Any:
    with httpx.Client(timeout=30) as client:
        r = client.patch(url, headers=headers, json=data)
        r.raise_for_status()
        return r.json() if r.content else None


def delete(url: str, headers: dict) -> Any:
    with httpx.Client(timeout=30) as client:
        r = client.delete(url, headers=headers)
        if r.status_code == 204:
            return None
        r.raise_for_status()
        return r.json() if r.content else None


# =============================================================================
# PROJECTS
# =============================================================================

@mcp.tool()
def list_projects() -> list[dict]:
    """List all projects in the workspace."""
    resp = get(api_v1("projects/"), api_v1_headers())
    return resp.get("results", resp) if isinstance(resp, dict) else resp


@mcp.tool()
def get_project(project_id: str) -> dict:
    """Get project details by ID."""
    return get(api_v1(f"projects/{project_id}/"), api_v1_headers())


# =============================================================================
# ISSUES (work items)
# =============================================================================

@mcp.tool()
def list_issues(
    project_id: str,
    assignee_id: str | None = None,
    state_id: str | None = None,
    priority: str | None = None,
    label_id: str | None = None,
) -> list[dict]:
    """
    List issues in a project. Optionally filter by assignee, state, priority, or label.
    Priority values: urgent, high, medium, low, none.
    """
    params: dict[str, str] = {}
    if assignee_id:
        params["assignees"] = assignee_id
    if state_id:
        params["state"] = state_id
    if priority:
        params["priority"] = priority
    if label_id:
        params["labels"] = label_id
    resp = get(api_v1(f"projects/{project_id}/issues/"), api_v1_headers(), params=params)
    return resp.get("results", resp) if isinstance(resp, dict) else resp


@mcp.tool()
def get_issue(project_id: str, issue_id: str) -> dict:
    """Get a single issue by ID."""
    return get(api_v1(f"projects/{project_id}/issues/{issue_id}/"), api_v1_headers())


@mcp.tool()
def create_issue(
    project_id: str,
    name: str,
    state: str | None = None,
    priority: str | None = None,
    assignees: list[str] | None = None,
    labels: list[str] | None = None,
    description_html: str | None = None,
    start_date: str | None = None,
    target_date: str | None = None,
    parent: str | None = None,
) -> dict:
    """
    Create a new issue in a project.

    Args:
        project_id: UUID of the project
        name: Issue title (required)
        state: UUID of the state (use list_states to get IDs)
        priority: urgent, high, medium, low, none
        assignees: List of user UUIDs
        labels: List of label UUIDs
        description_html: HTML description
        start_date: ISO date (YYYY-MM-DD)
        target_date: ISO date (YYYY-MM-DD)
        parent: UUID of parent issue
    """
    data: dict[str, Any] = {"name": name}
    if state:
        data["state"] = state
    if priority:
        data["priority"] = priority
    if assignees:
        data["assignees"] = assignees
    if labels:
        data["labels"] = labels
    if description_html:
        data["description_html"] = description_html
    if start_date:
        data["start_date"] = start_date
    if target_date:
        data["target_date"] = target_date
    if parent:
        data["parent"] = parent
    return post(api_v1(f"projects/{project_id}/issues/"), api_v1_headers(), data)


@mcp.tool()
def update_issue(
    project_id: str,
    issue_id: str,
    name: str | None = None,
    state: str | None = None,
    priority: str | None = None,
    assignees: list[str] | None = None,
    labels: list[str] | None = None,
    description_html: str | None = None,
    start_date: str | None = None,
    target_date: str | None = None,
    parent: str | None = None,
) -> dict:
    """Update an existing issue. Only provided fields will be changed."""
    data: dict[str, Any] = {}
    if name is not None:
        data["name"] = name
    if state is not None:
        data["state"] = state
    if priority is not None:
        data["priority"] = priority
    if assignees is not None:
        data["assignees"] = assignees
    if labels is not None:
        data["labels"] = labels
    if description_html is not None:
        data["description_html"] = description_html
    if start_date is not None:
        data["start_date"] = start_date
    if target_date is not None:
        data["target_date"] = target_date
    if parent is not None:
        data["parent"] = parent
    return patch(api_v1(f"projects/{project_id}/issues/{issue_id}/"), api_v1_headers(), data)


@mcp.tool()
def delete_issue(project_id: str, issue_id: str) -> str:
    """Delete an issue by ID."""
    delete(api_v1(f"projects/{project_id}/issues/{issue_id}/"), api_v1_headers())
    return "Deleted"


# =============================================================================
# STATES
# =============================================================================

@mcp.tool()
def list_states(project_id: str) -> list[dict]:
    """List all states (statuses) in a project."""
    resp = get(api_v1(f"projects/{project_id}/states/"), api_v1_headers())
    return resp.get("results", resp) if isinstance(resp, dict) else resp


# =============================================================================
# LABELS
# =============================================================================

@mcp.tool()
def list_labels(project_id: str) -> list[dict]:
    """List all labels in a project."""
    resp = get(api_v1(f"projects/{project_id}/labels/"), api_v1_headers())
    return resp.get("results", resp) if isinstance(resp, dict) else resp


@mcp.tool()
def create_label(project_id: str, name: str, color: str = "#000000") -> dict:
    """Create a new label in a project."""
    return post(api_v1(f"projects/{project_id}/labels/"), api_v1_headers(), {"name": name, "color": color})


# =============================================================================
# MEMBERS
# =============================================================================

@mcp.tool()
def list_members(project_id: str) -> list[dict]:
    """List all members of a project."""
    resp = get(api_v1(f"projects/{project_id}/members/"), api_v1_headers())
    return resp.get("results", resp) if isinstance(resp, dict) else resp


# =============================================================================
# CYCLES
# =============================================================================

@mcp.tool()
def list_cycles(project_id: str) -> list[dict]:
    """List all cycles in a project."""
    resp = get(api_v1(f"projects/{project_id}/cycles/"), api_v1_headers())
    return resp.get("results", resp) if isinstance(resp, dict) else resp


# =============================================================================
# MODULES
# =============================================================================

@mcp.tool()
def list_modules(project_id: str) -> list[dict]:
    """List all modules in a project."""
    resp = get(api_v1(f"projects/{project_id}/modules/"), api_v1_headers())
    return resp.get("results", resp) if isinstance(resp, dict) else resp


# =============================================================================
# PAGES (requires session cookie — /api/ without v1)
# =============================================================================

@mcp.tool()
def list_pages(project_id: str) -> list[dict]:
    """List all pages in a project. Requires session cookie."""
    resp = get(api_internal(f"projects/{project_id}/pages/"), session_headers())
    return resp.get("results", resp) if isinstance(resp, dict) else resp


@mcp.tool()
def get_page(project_id: str, page_id: str) -> dict:
    """Get a page by ID. Requires session cookie."""
    return get(api_internal(f"projects/{project_id}/pages/{page_id}/"), session_headers())


@mcp.tool()
def create_page(
    project_id: str,
    name: str,
    description_html: str = "<p></p>",
    access: int = 0,
) -> dict:
    """
    Create a new page in a project. Requires session cookie.

    Args:
        project_id: UUID of the project
        name: Page title
        description_html: HTML content of the page
        access: 0 = public, 1 = private
    """
    data = {"name": name, "description_html": description_html, "access": access}
    return post(api_internal(f"projects/{project_id}/pages/"), session_headers(), data)


@mcp.tool()
def update_page(
    project_id: str,
    page_id: str,
    name: str | None = None,
    description_html: str | None = None,
) -> dict:
    """Update a page. Requires session cookie."""
    data: dict[str, Any] = {}
    if name is not None:
        data["name"] = name
    if description_html is not None:
        data["description_html"] = description_html
    return patch(api_internal(f"projects/{project_id}/pages/{page_id}/"), session_headers(), data)


# =============================================================================
# USERS (requires session cookie — /api/ without v1)
# =============================================================================

@mcp.tool()
def get_me() -> dict:
    """Get current user information. Requires session cookie."""
    return get(f"{BASE_URL}/api/users/me/", session_headers())


# =============================================================================
# Entry point
# =============================================================================

if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "sse":
        import uvicorn
        app = mcp.sse_app()
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=int(os.getenv("MCP_PORT", "8000")),
            forwarded_allow_ips="*",
        )
    else:
        mcp.run(transport="stdio")
