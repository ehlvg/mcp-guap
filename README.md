# mcp-guap

MCP-сервер для личного кабинета ГУАП ([pro.guap.ru](https://pro.guap.ru)).
Позволяет ИИ-агентам (Claude и другим) работать с заданиями, материалами и отчётами студента.

## Что умеет

| Инструмент | Описание |
|---|---|
| `list_tasks` | Список всех заданий текущего семестра (дедлайны, баллы, статусы) |
| `get_task` | Детали задания: описание, доп. материалы, сданные отчёты |
| `list_materials` | Учебные материалы семестра (файлы и внешние ссылки) |
| `download_material` | Скачать учебный материал (с pro.guap.ru, Google Drive или любой ссылке) |
| `submit_report` | Загрузить файл отчёта к заданию |

## Требования

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — менеджер пакетов Python
- [Claude Desktop](https://claude.ai/download) (или любой другой MCP-клиент)
- Аккаунт ГУАП на [pro.guap.ru](https://pro.guap.ru)

## Установка

Клонировать репозиторий не нужно — достаточно `uv`.

**1. Получить куки из браузера**

1. Войдите в [pro.guap.ru](https://pro.guap.ru) в браузере
2. Откройте DevTools → вкладка **Network**
3. Обновите страницу, кликните на любой запрос к `pro.guap.ru`
4. В заголовках запроса найдите **Cookie** и скопируйте всё значение

**2. Добавить сервер в Claude Desktop**

Откройте файл конфигурации Claude Desktop:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Добавьте секцию `mcpServers` (или дополните существующую):

```json
{
  "mcpServers": {
    "guap": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/ehlvg/mcp-guap", "mcp-guap"],
      "env": {
        "GUAP_COOKIE": "YOUR_COOKIE_STRING_HERE"
      }
    }
  }
}
```

Замените `YOUR_COOKIE_STRING_HERE` на скопированное значение Cookie.

**3. Перезапустить Claude Desktop**

После перезапуска в Claude появятся инструменты `list_tasks`, `get_task`, `list_materials`, `download_material`, `submit_report`.

> Куки живут несколько часов. Когда перестанет работать — обновите `GUAP_COOKIE` в конфиге и перезапустите Claude Desktop.

## Использование

Просто общайтесь с Claude на естественном языке:

> «Покажи все мои задания»
> «Что нужно сдать по вычислительной математике?»
> «Загрузи файл ~/Documents/report.pdf как отчёт к заданию 181395»

## Запуск вручную (для отладки)

```bash
GUAP_COOKIE="..." uvx --from git+https://github.com/ehlvg/mcp-guap mcp-guap
```

## Структура проекта

```
mcp-guap/
├── mcp_guap/
│   ├── server.py        # MCP-сервер, определение инструментов
│   └── guap_client.py   # HTTP-клиент и парсеры HTML
├── pyproject.toml       # Зависимости проекта
└── cookie.txt           # Ваши куки (не коммитится, опционально)
```
