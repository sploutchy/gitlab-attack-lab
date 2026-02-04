# GitLab Attack Lab - Web Application

A minimal Laravel-based web application that displays scenario markdown files and allows flag validation using regex patterns.

## Features

- 📖 **Markdown Scenarios**: Display rich scenario content from markdown files
- 🚩 **Flag Validation**: Validate submitted flags using regex patterns
- 💾 **Session-Based Progress**: Track found flags in browser session
- 🎨 **Daisy UI Design**: Modern, responsive UI with Tailwind CSS
- ⚡ **Alpine.js Interactivity**: Fast, lightweight client-side interactions
- 🐳 **Docker Integration**: Automatically starts with `make setup`

## Architecture

The web app is built with:
- **Backend**: Laravel 11 with PHP 8.3
- **Frontend**: Alpine.js + Daisy UI + Tailwind CSS
- **Markdown**: Parsedown for rendering markdown to HTML
- **Storage**: Session-based (no database required)

## Directory Structure

```
app/
├── app/
│   ├── Http/Controllers/ScenarioController.php
│   └── Services/
│       ├── ScenarioService.php         # Load scenarios from markdown
│       └── FlagValidationService.php   # Validate flags with regex
├── bootstrap/app.php
├── config/                             # Laravel configuration
│   ├── app.php
│   ├── cache.php
│   ├── logging.php
│   └── session.php
├── docker/
│   ├── Dockerfile                      # Docker container setup
│   └── entrypoint.sh                   # Startup script
├── resources/
│   ├── css/app.css
│   ├── js/app.js
│   └── views/
│       ├── layouts/app.blade.php
│       ├── index.blade.php             # Home page
│       └── scenario.blade.php          # Scenario view
├── routes/
│   ├── web.php                         # Web routes
│   └── console.php
├── .env.example
├── composer.json
├── package.json
├── postcss.config.js
├── tailwind.config.js
└── vite.config.js
```

## Scenario Format

Scenarios are markdown files with YAML frontmatter in `lab-config/scenarios/`:

```markdown
---
id: scenario-01
title: CI/CD Variables Exposure
difficulty: intermediate
order: 1
flags:
  - name: API Key Flag
    pattern: "^flag\\{[a-z0-9_]{32}\\}$"
  - name: Database Password
    pattern: "^flag\\{db_[a-z0-9]{16}\\}$"
---

# CI/CD Variables Exposure

## Objective
Learn how to find and exploit exposed CI/CD variables...

## Steps
1. Login to GitLab
2. Navigate to the web-app project
3. Check the pipeline output for exposed variables
```

### Frontmatter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique scenario identifier (e.g., `scenario-01`) |
| `title` | string | Yes | Scenario title for display |
| `difficulty` | string | No | `beginner`, `intermediate`, or `advanced` (default: `beginner`) |
| `order` | number | No | Display order (default: 999) |
| `flags` | array | No | Array of flag definitions |
| `flags[].name` | string | Yes | Flag name for display |
| `flags[].pattern` | string | Yes | Regex pattern to match the flag |

## Routes

### Web Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Home page with scenario list |
| `/scenarios/{slug}` | GET | View scenario with markdown content |
| `/scenarios/{slug}/validate` | POST | Validate submitted flag (AJAX) |

### API Response Format

**Success Response**:
```json
{
  "success": true,
  "message": "✓ Correct! Flag found: API Key Flag",
  "found_count": 1,
  "total_flags": 2
}
```

**Error Response**:
```json
{
  "success": false,
  "message": "Incorrect flag. Try again or check the hints in the scenario."
}
```

## Getting Started

### Prerequisites
- Docker and Docker Compose installed
- Running GitLab instance (started with `make setup`)

### Starting the Lab

The web app automatically starts when you run:

```bash
make setup
```

Or manually start it:

```bash
make start
```

Access the web app at: **http://127.0.0.1:8080**

### Management Commands

```bash
# Enter the web app container
make lab-web-shell

# View web app logs
make lab-web-logs

# Stop the lab
make stop

# Destroy the lab (remove all data)
make destroy
```

## Creating a New Scenario

1. Create a markdown file in `lab-config/scenarios/`:

```bash
cat > lab-config/scenarios/scenario-02-runner-secrets.md << 'EOF'
---
id: scenario-02
title: Runner Configuration Secrets
difficulty: intermediate
order: 2
flags:
  - name: Runner Token
    pattern: "^glrt-[a-zA-Z0-9_-]{20,}$"
---

# Runner Configuration Secrets

## Objective
Learn how to access and exploit GitLab runner configurations...

## Steps
1. Login as pentester
2. Access the runner configuration
3. Extract the token from the configuration file
EOF
```

2. The scenario will automatically appear on the home page

## Services

The web app container is defined in `docker-compose.yml`:

```yaml
lab-web:
  build:
    context: ./app
    dockerfile: docker/Dockerfile
  container_name: lab-web-app
  ports:
    - "8080:8000"
  volumes:
    - ./app:/app
    - ./lab-config/scenarios:/app/scenarios:ro
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000"]
```

## Key Files

### Services (app/Services/)
- **ScenarioService.php**: Loads scenarios from markdown files with YAML frontmatter
- **FlagValidationService.php**: Validates submitted flags against regex patterns

### Controller (app/Http/Controllers/)
- **ScenarioController.php**: Handles all routing and rendering

### Views (resources/views/)
- **layouts/app.blade.php**: Master layout with Daisy UI
- **index.blade.php**: Home page with scenario cards
- **scenario.blade.php**: Scenario detail page with flag form and sidebar

### Frontend (resources/)
- **js/app.js**: Alpine.js components for flag submission
- **css/app.css**: Markdown styling and animations

## Development

### Rebuilding Assets

If you modify CSS or JavaScript:

```bash
make lab-web-shell
npm run build
```

### Debugging

Add `APP_DEBUG=true` to the `.env` file to enable debug mode:

```bash
make lab-web-shell
# Edit .env file
vi .env
```

### Testing Locally (without Docker)

```bash
cd app
composer install
npm install && npm run build
php artisan serve
```

Access at: http://localhost:8000

## Troubleshooting

### Web app not starting

```bash
# Check logs
make lab-web-logs

# Check if container is running
make status

# Restart the service
docker-compose restart lab-web
```

### Scenario files not loading

1. Ensure markdown files are in `lab-config/scenarios/`
2. Verify YAML frontmatter is valid
3. Check the container has read access:
   ```bash
   docker-compose exec lab-web ls -la /app/scenarios/
   ```

### Flag validation not working

1. Check the regex pattern in the scenario file
2. Test the pattern:
   ```bash
   make lab-web-shell
   php artisan tinker
   > preg_match('/^flag\{[a-z0-9]{16}\}$/', 'flag{abc123def456gh}')
   ```

## Performance

- Page load time: < 1 second
- Session handling: Cookie-based
- No database queries

## Security Notes

- No user authentication (anonymous access)
- Session data stored in cookies
- Flag patterns are regex patterns (no SQL injection possible)
- CSRF protection enabled for form submissions
- Flag validation happens server-side only

## Future Enhancements

- User accounts and progress persistence
- Leaderboard
- Hint system with progressive reveals
- Team challenges
- Real-time notifications

## License

Same as GitLab Attack Lab

## Support

For issues or feature requests, please open an issue on the main GitLab Attack Lab repository.
