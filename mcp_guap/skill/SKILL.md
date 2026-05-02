---
name: guap
description: Access GUAP university personal cabinet (pro.guap.ru) to manage student tasks, materials, and reports. Use when the user needs to view assignments, deadlines, download learning materials, submit reports, or check their academic progress at GUAP university.
license: MIT
compatibility: Requires Python 3.12+, httpx, beautifulsoup4, lxml, and playwright for browser authentication. Works with any Agent Skills compatible client.
metadata:
  author: ehlvg
  version: "0.1.0"
  repository: https://github.com/ehlvg/mcp-guap
---

# GUAP Personal Cabinet Access

This skill provides access to the GUAP (Saint Petersburg State University of Aerospace Instrumentation) university personal cabinet at pro.guap.ru.

## Capabilities

- **Task Management**: List, view, and filter student assignments
- **Materials**: Access and download learning materials
- **Reports**: Submit assignment reports
- **Profile**: View student information

## When to Use This Skill

Activate this skill when the user:
- Mentions GUAP, pro.guap.ru, or their student account
- Asks about assignments, tasks, or deadlines
- Wants to download learning materials
- Needs to submit a report or check submission status
- Asks about their academic progress or profile information

## Authentication

Before using any commands, ensure the user is authenticated:

1. Check current auth status with `guap pro check`
2. If not authenticated, run `guap pro auth` to open browser login
3. The user will log in to pro.guap.ru in the browser window
4. Cookies are saved automatically for subsequent requests

## Available Commands

### Authentication
```bash
guap pro auth          # Authenticate via browser (interactive)
guap pro check         # Check if authentication is valid
```

### Task Management
```bash
guap pro tasks                    # List all tasks
guap pro tasks --status 1         # Show only tasks without reports
guap pro tasks --subject 123      # Filter by subject ID
guap pro task 181395              # Get detailed task information
```

**Task Status Codes:**
- `0` - All tasks
- `1` - Without reports (не сдано)
- `2` - Pending review (ожидает проверки)
- `3` - Accepted (принято)
- `4` - Not accepted (не принято)
- `5` - All except accepted

### Materials
```bash
guap pro materials                # List all materials
guap pro materials --urls         # Include download URLs
guap pro materials --subject 123  # Filter by subject
```

### Profile
```bash
guap pro profile                  # Show student profile
```

## Common Workflows

### Check Today's Tasks
```bash
guap pro check                    # Verify auth
guap pro tasks --status 1         # Show incomplete tasks
```

### Submit a Report
1. Get task details: `guap pro task <ID>`
2. Check allowed file extensions in task details
3. Ensure file exists locally
4. Use MCP tool `submit_report` or manual upload via browser

### Download Materials
1. List materials: `guap pro materials --urls`
2. Download using URLs with `download_material` tool or browser

## Important Notes

- Session cookies expire after several hours
- Re-run `guap pro auth` when authentication expires
- Task IDs and Subject IDs are numeric
- File extensions for reports are restricted per task
- Downloaded materials are saved to `~/Downloads/guap-materials/` by default

## References

- [Command Reference](references/COMMANDS.md) - Detailed command documentation
- [API Notes](references/API.md) - Technical details about pro.guap.ru API
