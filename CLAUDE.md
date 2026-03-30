# Plane MCP-сервер (self-hosted)

Эта папка содержит кастомный MCP-сервер для интеграции с self-hosted Plane.

## Если пользователь просит настроить MCP / подключить Plane

Выполни следующие шаги:

### 1. Найди путь к uv

```bash
which uv || where uv
```

Если uv не найден — помоги установить:
- Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`
- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 2. Спроси у пользователя 3 вещи

Задай все три вопроса **одним сообщением**:

1. **API-ключ Plane** — его нужно создать в Plane: Профиль (левый нижний угол) → Profile settings → API tokens → Add API token. Ключ начинается с `plane_api_`
2. **Workspace Slug** — короткий идентификатор из URL: `https://plane.домен.ru/SLUG/projects/...`
3. **URL Plane** — адрес их Plane, например `https://plane.akfixdev.ru`

### 3. Определи абсолютный путь к этой папке

```bash
cd plane-mcp-selfhosted && pwd
```

### 4. Создай файл `.mcp.json` в корне проекта пользователя

```json
{
  "mcpServers": {
    "plane": {
      "type": "stdio",
      "command": "ПУТЬ_К_UV",
      "args": ["run", "--directory", "ПУТЬ_К_ЭТОЙ_ПАПКЕ", "python", "server.py"],
      "env": {
        "PLANE_API_KEY": "КЛЮЧ_ПОЛЬЗОВАТЕЛЯ",
        "PLANE_WORKSPACE_SLUG": "SLUG_ПОЛЬЗОВАТЕЛЯ",
        "PLANE_BASE_URL": "URL_ПОЛЬЗОВАТЕЛЯ"
      }
    }
  }
}
```

### 5. Попроси пользователя перезапустить IDE

Скажи: "Перезапустите VS Code / Cursor, чтобы MCP-сервер подключился. После этого я смогу работать с вашими задачами в Plane."

### Опционально: session cookie

Если пользователь хочет работать со **страницами (Pages)** — нужны cookie:
- Открыть Plane в Chrome → F12 → Application → Cookies
- Скопировать значения `session-id` и `csrftoken`
- Добавить в env: `PLANE_SESSION_COOKIE` и `PLANE_CSRF_TOKEN`
- Cookie живут ~7 дней, потом нужно обновить
