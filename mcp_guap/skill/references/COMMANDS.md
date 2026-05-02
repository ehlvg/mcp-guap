# GUAP CLI Command Reference

## guap pro auth

Authenticate with pro.guap.ru via browser automation.

**Usage:**
```bash
guap pro auth [--timeout SECONDS]
```

**Options:**
- `--timeout` - Authentication timeout in seconds (default: 120)

**Description:**
Opens a browser window and navigates to pro.guap.ru login page. User enters credentials manually. Upon successful login, session cookies are automatically saved to `cookie.json`.

**Exit Codes:**
- `0` - Authentication successful
- `1` - Authentication failed or timeout

---

## guap pro check

Check if current authentication is valid.

**Usage:**
```bash
guap pro check
```

**Description:**
Validates saved cookies by attempting to access the user profile page.

**Output:**
- ✅ Authentication valid
- ❌ Authentication invalid (with error details)

**Exit Codes:**
- `0` - Authentication valid
- `1` - Authentication invalid or not found

---

## guap pro tasks

List student tasks with optional filters.

**Usage:**
```bash
guap pro tasks [--semester ID] [--subject ID] [--type TYPE] [--status STATUS]
```

**Options:**
- `--semester ID` - Filter by semester ID (e.g., 27 for 2025/2026 spring)
- `--subject ID` - Filter by subject/discipline ID
- `--type TYPE` - Filter by task type (1-16)
  - 1: Course project (Курсовой проект)
  - 2: Lab work (Лабораторная работа)
  - 3: Essay (Реферат)
  - 4: Control work (Контрольная работа)
  - 5: Calculation-graphic work (Расчетно-графическая работа)
  - 6: Calculation task (Расчетное задание)
  - 7: Essay (Эссе)
  - 8: Practice report (Отчет о практике)
  - 9: Test work (Проверочная работа)
  - 10: Individual foreign language task
  - 11: Current testing (Текущее тестирование)
  - 12: Scientific report (Научный доклад)
  - 13: Scientific research report
  - 14: Individual task (Индивидуальное задание)
  - 15: Practical tasks (Практические задания)
  - 16: Class work (Работа на занятии)
- `--status STATUS` - Filter by status (0-5)
  - 0: All
  - 1: Without reports only
  - 2: Pending review
  - 3: Accepted only
  - 4: Not accepted only
  - 5: All except accepted

**Output:**
Table with columns: ID, Subject, Name, Status, Points, Deadline

---

## guap pro task

Get detailed information about a specific task.

**Usage:**
```bash
guap pro task <ID>
```

**Arguments:**
- `ID` - Task ID (numeric)

**Output:**
- Task name and ID
- Subject and type
- Teacher information
- Maximum points
- Deadline
- Full description
- Allowed file extensions
- Extra materials with links
- Submitted reports with status

---

## guap pro materials

List learning materials.

**Usage:**
```bash
guap pro materials [--semester ID] [--subject ID] [--urls]
```

**Options:**
- `--semester ID` - Filter by semester ID
- `--subject ID` - Filter by subject ID
- `--urls` - Include download URLs in output

**Output:**
Table with columns: Subject, Name, Teacher, Date Added

---

## guap pro profile

Display student profile information.

**Usage:**
```bash
guap pro profile
```

**Output:**
- Full name (ФИО)
- Group
- Student ID number
- Institute/Faculty
- Specialty
- Study form
- Education level
- Status
