"""MCP server for GUAP personal cabinet (pro.guap.ru)"""

import os
from pathlib import Path
from typing import Optional

from mcp.server.fastmcp import FastMCP
from mcp import McpError
from mcp.types import ErrorData, INTERNAL_ERROR, INVALID_PARAMS

try:
    from . import guap_client as gc
except ImportError:
    import guap_client as gc  # type: ignore[no-redef]

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

    for config_path in (
        Path(__file__).parent / "cookie.txt",
        Path(__file__).parent.parent / "cookie.txt",
    ):
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
    "Get the current student's profile: full name (ФИО), group, student book number, "
    "institute, specialty, study form, education level, and enrollment status."
))
def get_my_profile() -> dict:
    cookie = _get_cookie()
    try:
        p = gc.get_profile(cookie)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch profile: {e}"))

    return {
        "full_name": p.full_name,
        "group": p.group,
        "student_id": p.student_id,
        "institute": p.institute,
        "specialty": p.specialty,
        "direction": p.direction,
        "study_form": p.study_form,
        "education_level": p.education_level,
        "status": p.status,
    }


@mcp.tool(description=(
    "Get information about a teacher by their numeric profile ID. "
    "Returns full name (ФИО), academic degree/rank, and list of positions "
    "(each with position title, department, and organization). "
    "Teacher IDs are available in list_tasks, get_task, and list_materials results."
))
def get_teacher_info(teacher_id: str) -> dict:
    cookie = _get_cookie()
    try:
        t = gc.get_teacher_profile(cookie, int(teacher_id))
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch teacher {teacher_id}: {e}"))

    return {
        "teacher_id": t.teacher_id,
        "full_name": t.full_name,
        "degree": t.degree,
        "positions": t.positions,
    }


@mcp.tool(description=(
    "Get detailed information about a specific subject/discipline by its numeric ID. "
    "Returns name, department (кафедра), year and semester, control type (экзамен/зачёт/КП etc.), "
    "current grade, total hours, and the assigned teacher with their position. "
    "Subject IDs are available in list_tasks, get_task, and list_materials results."
))
def get_subject_info(subject_id: str) -> dict:
    cookie = _get_cookie()
    try:
        s = gc.get_subject(cookie, int(subject_id))
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch subject {subject_id}: {e}"))

    return {
        "subject_id": s.subject_id,
        "name": s.name,
        "department": s.department,
        "year_semester": s.year_semester,
        "control_type": s.control_type,
        "grade": s.grade,
        "hours": s.hours,
        "teacher": s.teacher,
        "teacher_id": s.teacher_id,
        "teacher_position": s.teacher_position,
        "lesson_types": s.lesson_types,
        "groups": s.groups,
    }


@mcp.tool(description=(
    "Get the current student's order number (порядковый номер) in the group list. "
    "Also returns the total number of students in the group, the student's full name, "
    "and the group name."
))
def get_my_group_order() -> dict:
    cookie = _get_cookie()
    try:
        return gc.get_group_order(cookie)
    except Exception as e:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"Failed to fetch group order: {e}"))


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
