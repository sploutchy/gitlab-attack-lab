# GitLab Attack Lab - Web Application Mini Project Plan

## Overview
A minimal Laravel-based web application with Daisy UI that displays scenario markdown files and allows flag validation. No authentication, no database, no user accounts—just simple scenario viewing and flag checking.

---

## 1. Architecture & Design

### 1.1 System Architecture
```
┌────────────────────────────────────────────────────┐
│         Docker Compose Network                      │
├────────────────────────────────────────────────────┤
│                                                    │
│  ┌──────────────────┐    ┌──────────────────┐    │
│  │  Lab Web App     │    │  GitLab Instance │    │
│  │  (Laravel+Daisy) │───→│  (CE)            │    │
│  │  :8080           │    │  :80             │    │
│  └──────────────────┘    └──────────────────┘    │
│         │                                         │
│         │ Reads from                             │
│         │ lab-config/scenarios/                  │
│         │                                         │
│      └──────────────────────────┘                │
└────────────────────────────────────────────────────┘
```

### 1.2 Core Components

| Component | Purpose | Technology |
|-----------|---------|-----------|
| **Web Server** | Serve Laravel app | Laravel 11 + PHP 8.3 |
| **Frontend** | Responsive UI | Daisy UI + Tailwind + Alpine.js |
| **Markdown Rendering** | Parse and render scenario docs | Parsedown (PHP markdown parser) |
| **Flag Validation** | Check submitted flags against regex | Simple regex matching |
| **Session Storage** | Track found flags (temp) | PHP sessions |

---

## 2. Data Structure

### 2.1 File-Based Scenario Format

Scenarios are **markdown files** in `lab-config/scenarios/`:

```
lab-config/scenarios/
├── scenario-01-cicd-variables-exposure.md
├── scenario-02-runner-secrets.md
└── scenario-03-webhook-abuse.md
```

### 2.2 Scenario YAML Frontmatter

Each markdown file starts with YAML frontmatter containing flag definitions:

```markdown
---
id: scenario-01
title: CI/CD Variables Exposure
difficulty: intermediate
flags:
  - name: API Key Flag
    pattern: "^flag\\{[a-z0-9_]{32}\\}$"
  - name: Database Password
    pattern: "^flag\\{db_[a-z0-9]{16}\\}$"
---

# CI/CD Variables Exposure

## Objective
In this scenario, you'll learn how GitLab CI/CD variables can be exposed...

## Background
GitLab CI/CD pipelines often contain sensitive information...

## Steps
1. Login to GitLab
2. Navigate to the web-app project
3. View the pipeline output...

## Hints
- Check the pipeline output in GitLab
- Look for echo statements that might leak secrets
- The flag format is: flag{...}
```

---

## 3. Directory Structure

```
app/
├── Http/
│   ├── Controllers/
│   │   └── ScenarioController.php
│   └── Middleware/
│       └── SetJsonRequestHeader.php
├── Models/
│   └── Scenario.php (simple data model)
├── Services/
│   ├── ScenarioService.php (markdown loading)
│   └── FlagValidationService.php (regex matching)
├── resources/
│   ├── views/
│   │   ├── layouts/app.blade.php
│   │   ├── index.blade.php
│   │   ├── scenario.blade.php
│   │   └── components/
│   │       └── flag-form.blade.php
│   └── css/
│       └── app.css
├── routes/
│   └── web.php
├── docker/
│   ├── Dockerfile
│   ├── php.ini
│   └── entrypoint.sh
└── docker-compose.yml (updated)
```

---

## 4. Feature Specifications

### 4.1 Home Page
**Route**: `/`

- Scenarios list
- Simple cards with:
  - Scenario title
  - Difficulty badge
  - "View" button

### 4.2 Scenario Page
**Route**: `/scenarios/{slug}`

**Single Column Layout**:
- Markdown content (rendered from `.md` file)
- "Flags Found" counter (X / Y)
- Flag submission form:
  - Text input for flag
  - Submit button
  - Success/error feedback message
  - Clear button

**Flag Validation**:
- User enters flag
- Checked against regex patterns from frontmatter
- Shows success message if correct
- Shows error if incorrect
- Counts valid flags submitted
- Displays all found flags at top

---

## 5. API Endpoints

### 5.1 Web Routes

```
GET     /                          - Home / scenarios list
GET     /scenarios/{slug}          - View scenario markdown + submit flags
POST    /scenarios/{slug}/validate - Validate flag submission (AJAX)
```

### 5.2 Request/Response Format

**Flag Submission (AJAX POST)**:
```
POST /scenarios/scenario-01/validate

Request:
{
  "flag": "flag{secret_value}"
}

Response (Success):
{
  "success": true,
  "message": "Correct! Flag accepted.",
  "total_flags": 2,
  "found_flags": 2
}

Response (Error):
{
  "success": false,
  "message": "Incorrect flag. Try again or check the hints."
}
```

---

## 6. Technology Stack Details

### 6.1 Backend (Laravel 11)
```
- PHP 8.3
- Laravel Framework 11.x
- Parsedown (markdown parsing)
- YAML parsing for frontmatter
```

### 6.2 Frontend (Daisy UI)
```
- Alpine.js (lightweight interactivity for flag form)
- Tailwind CSS (styling)
- Daisy UI Components:
  - Card (scenario card)
  - Button (submit button)
  - Input (flag input)
  - Badge (difficulty, flag counter)
  - Alert (error/success messages)
```

### 6.3 No Database
```
- No database required
- Scenarios are markdown files in lab-config/scenarios/
- Session storage (PHP sessions) for temporary flag tracking
```

---

## 7. Docker Integration

### 7.1 Docker Compose Service

```yaml
lab-web:
  build:
    context: ./app
    dockerfile: docker/Dockerfile
  container_name: lab-web-app
  ports:
    - "8080:8000"
  environment:
    - APP_NAME=GitLab_Attack_Lab
    - APP_ENV=production
    - APP_DEBUG=false
    - SESSION_DRIVER=cookie
  networks:
    - lab-network
  volumes:
    - ./app:/app
    - ./lab-config/scenarios:/app/scenarios:ro
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### 7.2 Dockerfile

```dockerfile
FROM php:8.3-fpm

RUN apt-get update && apt-get install -y \
    curl \
    git \
    && docker-php-ext-install pdo

COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

WORKDIR /app

COPY . .

RUN composer install --no-dev --optimize-autoloader && \
    npm install && npm run build

EXPOSE 8000

ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["php", "artisan", "serve", "--host=0.0.0.0"]
```

---

## 8. Implementation Phases

### Phase 1: Foundation (1-2 days)
- [ ] Create Laravel project structure
- [ ] Set up Daisy UI layout
- [ ] Create ScenarioService to load markdown files
- [ ] Implement flag validation regex matching
- [ ] Docker setup and Compose configuration

### Phase 2: Core Features (1-2 days)
- [ ] Home page with scenario listing
- [ ] Scenario detail page with markdown rendering
- [ ] Flag submission form (AJAX)
- [ ] Session-based flag tracking
- [ ] Success/error message feedback

### Phase 3: Polish (1 day)
- [ ] Responsive design (mobile)
- [ ] Error handling
- [ ] Documentation

---

## 9. Integration with Existing Lab

### 9.1 Data Flow

```
lab-config/scenarios/
    │
    ├─ scenario-01-cicd-variables-exposure.md
    ├─ scenario-02-*.md
    └─ ...
    │
    ▼
ScenarioService (reads markdown + frontmatter)
    │
    ▼
Web UI (Laravel + Daisy)
    │
    ├─ /
    ├─ /scenarios/{slug}
    └─ POST /scenarios/{slug}/validate
    │
    ▼
Session Storage (found flags)
```

### 9.2 Makefile Updates

Add new commands:
```makefile
lab-web-shell:
	@$(DOCKER_COMPOSE) exec lab-web bash

lab-web-logs:
	@$(DOCKER_COMPOSE) logs -f lab-web
```

### 9.3 YAML Seeding

Create artisan command:
```
php artisan scenarios:refresh
```

Reads from `lab-config/scenarios/*.yml` and:
- Deletes old scenarios from DB
- Creates new scenarios from YAML
- Creates associated flags
- Seeds with demonstration data

---

## 10. Flag Validation Strategy

### 10.1 Flag Format
```
flag{scenario_slug_flag_name_hash}

Example:
flag{scenario-01_env-vars_a1b2c3d4}
```

### 10.2 Validation Logic

```php
// FlagValidationService.php

1. Extract flag text from submission
2. Match against flag_pattern regex (from markdown frontmatter)
3. If match succeeds:
   - Mark as correct in session
   - Return success response
   - Show confirmation message
4. If no match:
   - Return error response
   - Show helpful message
```

### 10.3 Storage
- Flags found stored in PHP session
- Reset when session expires or user refreshes entirely

---

## 11. Development Checklist

### Backend Tasks
- [ ] Laravel project setup
- [ ] ScenarioService (load markdown files with YAML frontmatter)
- [ ] FlagValidationService (regex matching)
- [ ] ScenarioController (index, show)
- [ ] Flag validation endpoint (AJAX)
- [ ] Session management

### Frontend Tasks
- [ ] Master layout with Daisy UI
- [ ] Home page with scenario list
- [ ] Scenario detail page with markdown rendering
- [ ] Flag submission form with Alpine.js
- [ ] Success/error messages
- [ ] Flag counter display
- [ ] Responsive design

### DevOps Tasks
- [ ] Dockerfile for Laravel app
- [ ] Docker Compose service configuration
- [ ] Environment configuration (.env.example)
- [ ] Entrypoint script
- [ ] Health checks

### Documentation
- [ ] Markdown scenario format guide
- [ ] How to add a new scenario
- [ ] Deployment instructions

---

## 12. Success Criteria

- [ ] Web app is accessible at http://127.0.0.1:8080
- [ ] Home page lists all scenarios
- [ ] Scenario markdown renders correctly
- [ ] Flag submission works
- [ ] Correct flags are validated properly
- [ ] Incorrect flags show error message
- [ ] Found flags persist in session
- [ ] Responsive design on mobile
- [ ] Fast page load (< 1 second)

---

## 13. Technology Justification

| Technology | Why Chosen |
|-----------|-----------|
| **Laravel** | Lightweight, simple routing, Blade templates |
| **Parsedown** | Lightweight markdown parser, no external dependencies |
| **Daisy UI** | Minimal CSS, great components, Tailwind-based |
| **Alpine.js** | Lightweight, vanilla JS, no build step needed |
| **No Database** | Simple file-based approach, less maintenance |

---

## 14. Estimated Effort

- **Development Time**: 3-4 days (1 person)
- **Estimated LOC**: ~1,500 backend + 1,000 frontend
- **Complexity**: Low
- **Maintenance**: Minimal (YAML file additions only)

---

## 15. Example Scenario File

Create `lab-config/scenarios/scenario-01-cicd-variables-exposure.md`:

```markdown
---
id: scenario-01
title: CI/CD Variables Exposure
difficulty: intermediate
flags:
  - name: Environment Variable Flag
    pattern: "^flag\\{env_[a-z0-9]{16}\\}$"
  - name: Secret Key Flag  
    pattern: "^flag\\{secret_[a-z0-9]{24}\\}$"
---

# CI/CD Variables Exposure

## Objective
Learn how to find and exploit exposed CI/CD variables in GitLab pipelines.

## Background
GitLab CI/CD pipelines often contain sensitive information like API keys, database passwords, and access tokens. 
When variables are exposed in logs or accessible to unauthorized users, they can be exploited.

## Steps to Find Flags

1. Login to GitLab at `http://127.0.0.1`
2. Navigate to the **web-app** project under the **development** group
3. Go to **CI/CD → Pipelines**
4. Click on the most recent pipeline
5. View the pipeline output logs
6. Look for exposed variables in the output
7. Copy the flag text and submit it below

## Hints

- Check the `deploy` job output
- Look for echo statements that print variables
- Environment variables might be exposed in error messages
```

