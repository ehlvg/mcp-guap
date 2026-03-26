"""HTTP client and HTML parsers for pro.guap.ru"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://pro.guap.ru"


@dataclass
class Task:
    task_id: int
    discipline: str
    discipline_id: Optional[int]
    name: str
    status: Optional[str]
    points_earned: Optional[str]
    points_max: Optional[str]
    task_type: str
    deadline: Optional[str]
    updated_at: str
    teacher: str
    teacher_id: Optional[int]


@dataclass
class TaskDetail:
    task_id: int
    name: str
    discipline: str
    discipline_id: Optional[int]
    task_type: str
    semester: str
    teacher: str
    teacher_id: Optional[int]
    points_max: Optional[str]
    order_num: Optional[str]
    added_at: Optional[str]
    allowed_extensions: str
    deadline: Optional[str]
    description: str
    extra_materials: list[dict]
    reports: list[dict]
    csrf_token: str


@dataclass
class Material:
    download_url: str
    external_url: Optional[str]
    discipline: str
    discipline_id: Optional[int]
    name: str
    added_at: str
    teacher: str
    teacher_id: Optional[int]


def _href_id(href: Optional[str], prefix: str) -> Optional[int]:
    if not href:
        return None
    m = re.search(rf"{re.escape(prefix)}(\d+)", href)
    return int(m.group(1)) if m else None


def _make_client(cookie: str) -> httpx.Client:
    return httpx.Client(
        base_url=BASE_URL,
        headers={
            "Cookie": cookie,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        },
        follow_redirects=True,
        timeout=30,
    )


def get_tasks(cookie: str, semester: Optional[int] = None) -> list[Task]:
    """Fetch all tasks for the given (or default current) semester."""
    params: dict = {}
    if semester is not None:
        params["semester"] = semester

    with _make_client(cookie) as client:
        r = client.get("/inside/student/tasks/", params=params)
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    # Find semester value from the selected option if not supplied
    if semester is None:
        sel = soup.select_one("select[name='semester'] option[selected]")
        if not sel:
            # first semester option
            sel = soup.select_one("select[name='semester'] option")

    tasks: list[Task] = []
    table = soup.select_one("table")
    if not table:
        return tasks

    for row in table.select("tr"):
        cells = row.select("td, th")
        if not cells or cells[0].name == "th":
            continue
        # Layout (10 columns):
        # 0: icon+link  1: Дисциплина  2: №в сем  3: Название  4: Статус
        # 5: Баллы  6: Тип  7: Предельная дата  8: Дата изменения  9: Преподаватель
        tds = row.select("td")
        if len(tds) < 4:
            continue

        task_link = tds[0].select_one("a")
        task_id_val = _href_id(task_link["href"] if task_link else None, "/inside/student/tasks/")

        disc_link = tds[1].select_one("a")
        discipline = disc_link.get_text(strip=True) if disc_link else ""
        discipline_id = _href_id(disc_link["href"] if disc_link else None, "/inside/students/subjects/")

        # tds[2] = № в сем (ignored)
        name_link = tds[3].select_one("a") if len(tds) > 3 else None
        name = name_link.get_text(strip=True) if name_link else (tds[3].get_text(strip=True) if len(tds) > 3 else "")

        status = tds[4].get_text(strip=True) or None if len(tds) > 4 else None
        points_raw = tds[5].get_text(strip=True) if len(tds) > 5 else ""
        task_type = tds[6].get_text(strip=True) if len(tds) > 6 else ""
        deadline = tds[7].get_text(strip=True) or None if len(tds) > 7 else None
        updated_at = tds[8].get_text(strip=True) if len(tds) > 8 else ""
        teacher_td = tds[9] if len(tds) > 9 else None

        points_parts = points_raw.split("/") if points_raw else []
        points_earned = points_parts[0].strip() if len(points_parts) == 2 else None
        points_max = points_parts[1].strip() if len(points_parts) == 2 else None

        teacher_link = teacher_td.select_one("a") if teacher_td else None
        teacher = teacher_link.get_text(strip=True) if teacher_link else ""
        teacher_id = _href_id(teacher_link["href"] if teacher_link else None, "/inside/profile/")

        if task_id_val is None:
            continue

        tasks.append(Task(
            task_id=task_id_val,
            discipline=discipline,
            discipline_id=discipline_id,
            name=name,
            status=status,
            points_earned=points_earned,
            points_max=points_max,
            task_type=task_type,
            deadline=deadline if deadline and deadline != "Не указана" else None,
            updated_at=updated_at,
            teacher=teacher,
            teacher_id=teacher_id,
        ))

    return tasks


def get_task(cookie: str, task_id: int) -> TaskDetail:
    """Fetch full details for a single task."""
    with _make_client(cookie) as client:
        r = client.get(f"/inside/student/tasks/{task_id}")
        r.raise_for_status()

    soup = BeautifulSoup(r.text, "lxml")

    # Task name: h3.page__title
    name_el = soup.select_one("h3.page__title")
    task_name = name_el.get_text(strip=True) if name_el else ""

    # Metadata: all h5 tags. Structure: "Key: <span>value</span>"
    disc_link = soup.select_one("h5 a[href*='/inside/students/subjects/']")
    discipline = disc_link.get_text(strip=True) if disc_link else ""
    discipline_id = _href_id(disc_link["href"] if disc_link else None, "/inside/students/subjects/")

    teacher_link = soup.select_one("h5 a[href*='/inside/profile/']")
    teacher = teacher_link.get_text(strip=True) if teacher_link else ""
    teacher_id = _href_id(teacher_link["href"] if teacher_link else None, "/inside/profile/")

    info: dict[str, str] = {}
    for h in soup.select("h5"):
        text = h.get_text(" ", strip=True)
        for key in ("Тип:", "Семестр:", "Баллы:", "№ задания:", "Дата добавления:",
                    "Доступные расширения файлов отчета:", "Предельная дата выполнения:"):
            if text.startswith(key):
                val_el = h.select_one("span")
                info[key] = val_el.get_text(strip=True) if val_el else text[len(key):].strip()

    # Description: <p> sibling after h5 "Описание задания"
    desc = ""
    for h in soup.select("h5"):
        if "Описание задания" in h.get_text():
            sibling = h.find_next_sibling()
            while sibling:
                t = sibling.get_text(" ", strip=True)
                if t:
                    desc = t
                    break
                sibling = sibling.find_next_sibling()
            break

    # Extra materials: links inside h5 "Доп. материалы"
    extra_materials = []
    for h in soup.select("h5"):
        if "Доп. материалы" in h.get_text():
            for a in h.select("a"):
                href = a.get("href", "")
                if href:
                    extra_materials.append({"text": a.get_text(strip=True), "url": href})
            break

    # Reports table: after h4 "Мои отчеты"
    reports = []
    for h in soup.select("h4"):
        if "Мои отчеты" in h.get_text():
            table = h.find_next("table")
            if table:
                for row in table.select("tr"):
                    tds = row.select("td")
                    if not tds:
                        continue
                    status = tds[0].get_text(strip=True)
                    file_link = tds[1].select_one("a") if len(tds) > 1 else None
                    href = file_link["href"] if file_link else ""
                    file_url = (BASE_URL + href if href.startswith("/") else href) if href else None
                    uploaded_at = tds[2].get_text(strip=True) if len(tds) > 2 else ""
                    checked_at = tds[3].get_text(strip=True) if len(tds) > 3 else ""
                    student_comment = tds[4].get_text(strip=True) if len(tds) > 4 else ""
                    teacher_comment = tds[5].get_text(strip=True) if len(tds) > 5 else ""
                    if status:
                        reports.append({
                            "status": status,
                            "file_url": file_url,
                            "uploaded_at": uploaded_at,
                            "checked_at": checked_at,
                            "student_comment": student_comment,
                            "teacher_comment": teacher_comment,
                        })
            break

    # CSRF token from the add-report form (only present when no report submitted yet)
    csrf_input = soup.select_one("#add-report-form input[name='token']")
    csrf_token = csrf_input["value"] if csrf_input else ""

    return TaskDetail(
        task_id=task_id,
        name=task_name,
        discipline=discipline,
        discipline_id=discipline_id,
        task_type=info.get("Тип:", ""),
        semester=info.get("Семестр:", ""),
        teacher=teacher,
        teacher_id=teacher_id,
        points_max=info.get("Баллы:", None),
        order_num=info.get("№ задания:", None),
        added_at=info.get("Дата добавления:", None),
        allowed_extensions=info.get("Доступные расширения файлов отчета:", "Все"),
        deadline=info.get("Предельная дата выполнения:", None) or None,
        description=desc,
        extra_materials=extra_materials,
        reports=reports,
        csrf_token=csrf_token,
    )


def get_materials(cookie: str) -> list[Material]:
    """Fetch all learning materials for the current semester."""
    all_materials: list[Material] = []
    page = 1

    with _make_client(cookie) as client:
        while True:
            r = client.get("/inside/student/materials", params={"page": page})
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")
            table = soup.select_one("table")
            if not table:
                break

            rows = table.select("tr")
            found_any = False
            for row in rows:
                tds = row.select("td")
                if not tds:
                    continue
                # Layout: [file-icon-link, external-link?, discipline, name, date, teacher]
                links_in_first = tds[0].select("a")
                download_url = ""
                external_url = None
                for a in links_in_first:
                    href = a.get("href", "")
                    if "/inside/student/materials/" in href and "/download" in href:
                        download_url = BASE_URL + href if href.startswith("/") else href
                    elif href.startswith("http"):
                        external_url = href

                # second <a> in first td may be external
                if not external_url and len(tds) > 1:
                    ext_a = tds[1].select_one("a")
                    if ext_a and ext_a.get("href", "").startswith("http"):
                        external_url = ext_a["href"]

                # Layout: 0=Файл/Ссылки, 1=Дисциплина, 2=Название, 3=Дата, 4=Преподаватель
                disc_link = tds[1].select_one("a") if len(tds) > 1 else None
                discipline = disc_link.get_text(strip=True) if disc_link else ""
                discipline_id = _href_id(disc_link["href"] if disc_link else None, "/inside/students/subjects/")

                name = tds[2].get_text(strip=True) if len(tds) > 2 else ""
                added_at = tds[3].get_text(strip=True) if len(tds) > 3 else ""
                teacher_td = tds[4] if len(tds) > 4 else None
                teacher_link = teacher_td.select_one("a") if teacher_td else None
                teacher = teacher_link.get_text(strip=True) if teacher_link else (teacher_td.get_text(strip=True) if teacher_td else "")
                teacher_id = _href_id(teacher_link["href"] if teacher_link else None, "/inside/profile/")

                if not name:
                    continue

                all_materials.append(Material(
                    download_url=download_url,
                    external_url=external_url,
                    discipline=discipline,
                    discipline_id=discipline_id,
                    name=name,
                    added_at=added_at,
                    teacher=teacher,
                    teacher_id=teacher_id,
                ))
                found_any = True

            # Check for next page
            next_link = soup.select_one("nav a[href*='page=']")
            if not next_link or not found_any:
                break
            page += 1

    return all_materials


def submit_report(cookie: str, task_id: int, file_path: str, comment: str = "") -> dict:
    """Submit a report file for a task. Returns result info."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with _make_client(cookie) as client:
        # Step 1: GET task page to extract CSRF token
        r = client.get(f"/inside/student/tasks/{task_id}")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        csrf_input = soup.select_one("#add-report-form input[name='token']")
        if not csrf_input:
            # Try any form with action matching store
            for form in soup.select("form"):
                if f"reports/{task_id}/store" in form.get("action", ""):
                    csrf_input = form.select_one("input[name='token']")
                    break

        if not csrf_input:
            raise RuntimeError("Could not find CSRF token on task page. Is the task accessible?")

        csrf_token = csrf_input["value"]

        # Step 2: POST multipart form with file
        with open(path, "rb") as f:
            r2 = client.post(
                f"/inside/student/reports/{task_id}/store",
                data={"token": csrf_token, "comment": comment},
                files={"file": (path.name, f, _guess_mime(path))},
            )
        r2.raise_for_status()

    # Parse response to check success
    soup2 = BeautifulSoup(r2.text, "lxml")
    # Look for error messages or success indicators
    error_els = soup2.select(".alert-danger, .error, .alert-error")
    success_els = soup2.select(".alert-success, .success")

    errors = [e.get_text(strip=True) for e in error_els if e.get_text(strip=True)]
    successes = [e.get_text(strip=True) for e in success_els if e.get_text(strip=True)]

    # If redirected back to task page and reports table has new entry — success
    new_reports_table = soup2.select_one("table")
    report_rows = new_reports_table.select("tr td") if new_reports_table else []

    return {
        "success": not errors,
        "errors": errors,
        "messages": successes,
        "final_url": str(r2.url),
    }


def _guess_mime(path: Path) -> str:
    ext = path.suffix.lower()
    types = {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".zip": "application/zip",
        ".rar": "application/x-rar-compressed",
        ".py": "text/x-python",
        ".txt": "text/plain",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    return types.get(ext, "application/octet-stream")
