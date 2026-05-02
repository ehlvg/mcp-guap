# GUAP API Technical Reference

## Base URL
```
https://pro.guap.ru
```

## Authentication

The API uses session-based authentication via cookies. After OAuth2 login through sso.guap.ru, the server sets session cookies that must be included in subsequent requests.

**Required Cookie:**
- PHP session cookies set after SSO authentication

**Cookie Format:**
```
Cookie: PHPSESSID=xxx; other_cookies=...
```

## OAuth2 Flow

1. User clicks "Login" on pro.guap.ru
2. Redirect to `https://sso.guap.ru/realms/master/protocol/openid-connect/auth`
3. User authenticates with GUAP credentials
4. Redirect back to `https://pro.guap.ru/oauth/callback`
5. Session cookies are set
6. User is authenticated for pro.guap.ru

## SSO Endpoints

### Token Endpoint
```
POST https://sso.guap.ru:8443/realms/master/protocol/openid-connect/token
```

**Parameters:**
- `client_id=prosuaiApi`
- `grant_type=password`
- `username` - GUAP login
- `password` - GUAP password
- `scope=openid email profile roles`

**Note:** OAuth2 tokens from SSO are not directly accepted by pro.guap.ru. Session cookies are required.

## HTML Structure

The site uses server-rendered HTML with tables for data display. Key selectors:

### Tasks Page (`/inside/student/tasks/`)
- Table: `table` - contains all tasks
- Rows: `tr` with `td` cells
- Columns: Icon, Subject, #, Name, Status, Points, Type, Deadline, Updated, Teacher

### Task Detail Page (`/inside/student/tasks/{id}`)
- Title: `h3.page__title`
- Metadata: `h5` tags with key-value pairs
- Description: `h5` containing "Описание задания" followed by content
- Materials: `h5` containing "Доп. материалы" with links
- Reports: `h4` containing "Мои отчеты" followed by table

### Materials Page (`/inside/student/materials`)
- Table: `table` - contains materials
- Pagination: `nav a[href*='page=']`

### Profile Page (`/inside/profile`)
- Name: `h3.text-center`
- Info: `h5` tags with labels like "Группа:", "Номер студенческого билета:"

## CSRF Protection

Forms include CSRF tokens:
- Input name: `token`
- Found in: `#add-report-form` or forms with `action*="reports/{id}/store"`

## File Upload

**Endpoint:**
```
POST /inside/student/reports/{task_id}/store
```

**Form Data:**
- `token` - CSRF token
- `comment` - Optional comment
- `file` - File content (multipart/form-data)

**Allowed Extensions:**
Per-task configuration. Common: `.pdf`, `.doc`, `.docx`, `.zip`
