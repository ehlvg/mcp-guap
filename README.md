# mcp-guap

MCP-сервер для личного кабинета ГУАП ([pro.guap.ru](https://pro.guap.ru)).
Позволяет ИИ-агентам (Claude и другим) работать с заданиями, материалами и отчётами студента.

## Что умеет

| Инструмент | Описание |
|---|---|
| `list_tasks` | Список всех заданий текущего семестра (дедлайны, баллы, статусы) |
| `get_task` | Детали задания: описание, доп. материалы, сданные отчёты |
| `list_materials` | Учебные материалы семестра (файлы и внешние ссылки) |
| `submit_report` | Загрузить файл отчёта к заданию |

## Требования

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — менеджер пакетов Python
- [Claude Desktop](https://claude.ai/download) (или любой другой MCP-клиент)
- Аккаунт ГУАП на [pro.guap.ru](https://pro.guap.ru)

## Установка

**1. Клонировать репозиторий**

```bash
git clone https://github.com/ehlvg/mcp-guap.git
cd mcp-guap
```

**2. Установить зависимости**

```bash
uv sync
```

**3. Получить куки из браузера**

1. Войдите в [pro.guap.ru](https://pro.guap.ru) в браузере
2. Откройте DevTools → вкладка **Network**
3. Обновите страницу, кликните на любой запрос к `pro.guap.ru`
4. В заголовках запроса найдите **Cookie** и скопируйте всё значение
5. Вставьте в файл `cookie.txt` в папке проекта:

```bash
echo "YOUR_COOKIE_STRING_HERE" > cookie.txt
```

> Куки живут несколько часов. Когда перестанет работать — повторите шаг 3–5.

**4. Добавить сервер в Claude Desktop**

Откройте файл конфигурации Claude Desktop:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Добавьте секцию `mcpServers` (или дополните существующую):

```json
{
  "mcpServers": {
    "guap": {
      "command": "/АБСОЛЮТНЫЙ/ПУТЬ/К/mcp-guap/.venv/bin/python3",
      "args": ["/АБСОЛЮТНЫЙ/ПУТЬ/К/mcp-guap/server.py"]
    }
  }
}
```

Узнать нужные пути можно командами:

```bash
# Python в виртуальном окружении
cd mcp-guap && uv run which python3

# Абсолютный путь к папке проекта
pwd
```

**5. Перезапустить Claude Desktop**

После перезапуска в Claude появятся инструменты `list_tasks`, `get_task`, `list_materials`, `submit_report`.

## Использование

Просто общайтесь с Claude на естественном языке:

> «Покажи все мои задания»
> «Что нужно сдать по вычислительной математике?»
> «Загрузи файл ~/Documents/report.pdf как отчёт к заданию 181395»

## Альтернативная аутентификация через переменную окружения

Вместо `cookie.txt` можно передать куки через `env` в конфиге:

```json
{
  "mcpServers": {
    "guap": {
      "command": "...",
      "args": ["..."],
      "env": {
        "GUAP_COOKIE": "YOUR_COOKIE_STRING_HERE"
      }
    }
  }
}
```

## Структура проекта

```
mcp-guap/
├── server.py        # MCP-сервер, определение инструментов
├── guap_client.py   # HTTP-клиент и парсеры HTML
├── pyproject.toml   # Зависимости проекта
└── cookie.txt       # Ваши куки (не коммитится, создайте сами)
```
