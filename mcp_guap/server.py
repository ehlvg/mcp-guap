"""MCP server for GUAP personal cabinet (pro.guap.ru)"""

import os
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp import McpError
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS

from . import guap_client as gc

mcp = FastMCP("guap", instructions=(
    "This server provides access to the GUAP university personal cabinet at pro.guap.ru. "
    "You can list tasks, get task details with materials links, list study materials, "
    "and submit report files for tasks."
))

# ---------------------------------------------------------------------------
# Auth helper
# ---------------------------------------------------------------------------

def _get_cookie() -> str:
    """Return the session cookie string from env or config file."""
    cookie = os.environ.get("GUAP_COOKIE", "").strip()
    if cookie:
        return cookie

    config_path = Path(__file__).parent / "cookie.txt"
    if config_path.exists():
        cookie = config_path.read_text().strip()
        if cookie:
            return cookie

    raise McpError(ErrorData(
        code=INVALID_PARAMS,
        message=(
            "GUAP session cookie not configured. "
            "Set the GUAP_COOKIE environment variable or create a cookie.txt file "
            "in the server directory with the full Cookie header value from your browser. "
            "To get it: open DevTools → Network → any request to pro.guap.ru → "
            "copy the 'Cookie' request header value."
        ),
    ))


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool(description=(
    "List all tasks assigned to the student for the current semester. "
    "Returns task id, discipline, name, status, points (earned/max), type, deadline, and teacher."
))
def list_tasks() -> list[dict]:
    cookie = _get_cookie()
    try:
        tasks = gc.get_tasks(cookie)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch tasks: {e}"))

    return [
        {
            "task_id": t.task_id,
            "discipline": t.discipline,
            "name": t.name,
            "status": t.status or "не сдано",
            "points": f"{t.points_earned or '0'} / {t.points_max or '?'}",
            "type": t.task_type,
            "deadline": t.deadline or "не указана",
            "updated_at": t.updated_at,
            "teacher": t.teacher,
        }
        for t in tasks
    ]


@mcp.tool(description=(
    "Get full details for a specific task by its numeric ID. "
    "Includes: description, allowed file extensions for the report, extra materials links, "
    "deadline, and the list of already submitted reports with their statuses."
))
def get_task(task_id: str) -> dict:
    cookie = _get_cookie()
    try:
        t = gc.get_task(cookie, int(task_id))
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch task {task_id}: {e}"))

    return {
        "task_id": t.task_id,
        "name": t.name,
        "discipline": t.discipline,
        "type": t.task_type,
        "semester": t.semester,
        "teacher": t.teacher,
        "points_max": t.points_max,
        "order_num": t.order_num,
        "added_at": t.added_at,
        "allowed_extensions": t.allowed_extensions,
        "deadline": t.deadline or "не указана",
        "description": t.description,
        "extra_materials": t.extra_materials,
        "submitted_reports": t.reports,
    }


@mcp.tool(description=(
    "List all learning materials available to the student for the current semester. "
    "Each material has a name, discipline, date added, teacher, and either a download URL "
    "(for files hosted on pro.guap.ru) or an external URL (Google Drive, etc.)."
))
def list_materials() -> list[dict]:
    cookie = _get_cookie()
    try:
        materials = gc.get_materials(cookie)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch materials: {e}"))

    return [
        {
            "name": m.name,
            "discipline": m.discipline,
            "added_at": m.added_at,
            "teacher": m.teacher,
            "download_url": m.download_url or m.external_url or "",
            "is_external": bool(not m.download_url and m.external_url),
        }
        for m in materials
    ]


@mcp.tool(description=(
    "Download a material file by URL. Works for three kinds of URLs: "
    "(1) pro.guap.ru internal links — authenticated automatically via the session cookie; "
    "(2) Google Drive share links (drive.google.com/file/d/...) — handles the confirmation page; "
    "(3) any other direct download URL (PDF, ZIP, etc.). "
    "The file is saved to ~/Downloads/guap-materials/ by default. "
    "Returns the local file path, filename, size in bytes, and content type."
))
def download_material(url: str, save_dir: Optional[str] = None) -> dict:
    cookie = _get_cookie()
    try:
        return gc.download_material(cookie, url, save_dir)
    except FileNotFoundError as e:
        raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
    except RuntimeError as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Download failed: {e}"))


@mcp.tool(description=(
    "Submit a report file for a specific task. "
    "The file must already exist on the local filesystem. "
    "Allowed extensions depend on the task — check get_task first. "
    "An optional comment can be included with the submission."
))
def submit_report(
    task_id: str,
    file_path: str,
    comment: Optional[str] = None,
) -> dict:
    cookie = _get_cookie()
    try:
        result = gc.submit_report(cookie, int(task_id), file_path, comment or "")
    except FileNotFoundError as e:
        raise McpError(ErrorData(code=INVALID_PARAMS, message=str(e)))
    except RuntimeError as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(e)))
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to submit report: {e}"))

    if not result["success"]:
        errors = "; ".join(result["errors"]) if result["errors"] else "Unknown error"
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Server rejected the report: {errors}"))

    return {
        "success": True,
        "message": "Report submitted successfully.",
        "messages": result["messages"],
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
