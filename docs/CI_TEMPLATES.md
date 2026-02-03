# CI/CD Template System

## Overview

The GitLab Attack Lab uses an external file-based CI/CD template system. All CI/CD pipeline configurations must be defined in separate YAML files within the `lab-config/ci-templates/` directory.

## Why External Templates?

1. **Avoids YAML Escaping Issues**: Complex bash scripts with special characters can cause YAML parsing errors when embedded inline
2. **Better Maintainability**: Easier to edit and version control pipeline configurations
3. **Validation**: Templates are validated before use to catch errors early
4. **Reusability**: Templates can be shared across multiple projects

## Directory Structure

```
lab-config/
├── ci-templates/           # All CI/CD pipeline templates
│   ├── web-app.yml
│   ├── api-service.yml
│   ├── mobile-app.yml
│   ├── infrastructure.yml
│   ├── security-tools.yml
│   ├── web-service.yml
│   ├── infrastructure-provisioner.yml
│   └── qa-automation.yml
├── scenarios/              # Scenario definitions reference templates
│   ├── default.yml
│   └── scenario-1.yml
└── base.yml
```

## Creating a CI Template

1. Create a new YAML file in `lab-config/ci-templates/`
2. Define your GitLab CI/CD pipeline using standard GitLab CI syntax
3. Reference the template in your scenario file

### Example Template

**File**: `lab-config/ci-templates/web-app.yml`

```yaml
image: node:18

stages:
  - test
  - build
  - deploy

cache:
  paths:
    - node_modules/

test:
  stage: test
  script:
    - npm ci
    - npm test
  tags:
    - docker

build:
  stage: build
  script:
    - npm run build
  artifacts:
    paths:
      - dist/
  tags:
    - docker

deploy:
  stage: deploy
  script:
    - echo "Deploying to $DEPLOY_ENV"
  only:
    - main
  tags:
    - docker
```

## Referencing Templates in Scenarios

In your scenario YAML file, reference the template using the `ci_cd_template` field:

```yaml
projects:
  - name: web-app
    path: web-app
    group: development-team
    visibility: private
    ci_cd_enabled: true
    ci_cd_template: "ci-templates/web-app.yml"  # Path relative to lab-config/
    variables:
      - key: DEPLOY_ENV
        value: production
```

## Important Notes

### ⚠️ Inline CI/CD Files Not Supported

The old `ci_cd_file` inline YAML approach is **deprecated and no longer supported**:

```yaml
# ❌ DEPRECATED - DO NOT USE
projects:
  - name: my-project
    ci_cd_file: |
      stages:
        - test
      # ...
```

Always use `ci_cd_template` instead:

```yaml
# ✅ CORRECT
projects:
  - name: my-project
    ci_cd_template: "ci-templates/my-project.yml"
```

## Validation

The populate script validates all CI templates before use:

1. **File Existence**: Ensures the template file exists
2. **Non-Empty**: Checks that the file is not empty
3. **Valid YAML**: Parses the YAML to ensure it's syntactically correct

If validation fails, you'll see an error message:

```
[   ERROR] CI template not found or invalid: ci-templates/missing.yml
```

## Testing

Run the CI template tests to ensure everything is configured correctly:

```bash
cd /workspaces/gitlab-attack-lab
python3 -m pytest tests/test_ci_templates.py -v
```

### Test Coverage

- ✅ Template file validation
- ✅ YAML syntax validation
- ✅ Empty file detection
- ✅ Missing file detection
- ✅ Integration: All referenced templates exist
- ✅ Integration: All templates have valid YAML
- ✅ Integration: No inline ci_cd_file usage

## Best Practices

### 1. Use Descriptive Filenames

Name templates after the project or purpose:
- `web-app.yml` for web applications
- `api-service.yml` for API services
- `mobile-app.yml` for mobile builds
- `infrastructure.yml` for IaC pipelines

### 2. Include All Required Fields

Ensure templates have:
- `stages`: Define pipeline stages
- Job definitions with `stage`, `script`, and `tags`
- Appropriate `only`/`except` rules for branch control

### 3. Use Variables Safely

When referencing CI/CD variables in templates, use safe defaults:

```yaml
script:
  - echo "Deploying to ${DEPLOY_ENV:-staging}"
  - echo "API Key: ${API_KEY:0:6}****"  # Only show first 6 chars
```

### 4. Tag Jobs Appropriately

Ensure jobs have appropriate runner tags:

```yaml
build:
  stage: build
  script:
    - make build
  tags:
    - docker    # For docker executor
    # or
    - shell    # For shell executor
```

### 5. Handle Complex Bash Carefully

For complex bash scripts with special characters, no quoting needed:

```yaml
script:
  - set -ex
  - for i in {1..100}; do echo "Processing $i"; done
  - cat > config.txt << 'EOF'
  - line1
  - line2
  - EOF
```

## Troubleshooting

### Template Not Found

**Error**: `CI template not found or invalid: ci-templates/my-template.yml`

**Solution**: Ensure the template file exists at `lab-config/ci-templates/my-template.yml`

### Invalid YAML Syntax

**Error**: `CI template validation failed: ... yaml.scanner.ScannerError`

**Solution**: Check your YAML syntax. Common issues:
- Incorrect indentation
- Missing colons
- Unbalanced quotes

### Pipeline Validation Errors in GitLab

If the pipeline fails to validate in GitLab after creation:
- Check GitLab syntax requirements
- Ensure all required jobs have `script` field
- Verify `stages` are defined before use
- Test locally with `gitlab-ci-lint` or online validator

## Migration from Inline CI Files

If you have existing inline `ci_cd_file` definitions:

1. Create a new template file in `lab-config/ci-templates/`
2. Copy the inline YAML content to the new file
3. Update the scenario to reference the template:
   ```yaml
   # Change from:
   ci_cd_file: |
     stages: ...
   
   # To:
   ci_cd_template: "ci-templates/project-name.yml"
   ```
4. Run tests to validate
5. Re-merge and re-populate GitLab

## See Also

- [GitLab CI/CD YAML Syntax Reference](https://docs.gitlab.com/ee/ci/yaml/)
- [GitLab CI/CD Variables](https://docs.gitlab.com/ee/ci/variables/)
- [GitLab Runner Configuration](https://docs.gitlab.com/runner/configuration/)
