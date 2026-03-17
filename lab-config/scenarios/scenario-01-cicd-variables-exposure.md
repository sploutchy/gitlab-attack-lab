---
id: scenario-01-cicd-variables-exposure
title: Sensitive Variable Exposure And Pipeleek Introduction
difficulty: beginner
order: 1
flags:
  - name: Variables Leak Flag
    pattern: "^flag\\{cicd_vars_[a-z0-9]{16}\\}$"
solution:
  title: Solution
  content: |
    1. Start the pentester container: `make shell`
    2. Configure the Pipeleek Personal Acces Token`
    3. Ensure to create the custom scan rule
    4. Use pipeleek to scan for variable leaks: `pipeleek scan`
    5. Submit the flag: `flag{cicd_vars_XXXXXXXXXXXXXXXX}`
hints:
  - title: Hint
    content: Configure Pipeleek according to the description, then run `pipeleek scan`.
---

## Objective

Identify how secrets can be exposed in CI/CD pipeline logs, get know Pipleek and its configuration and extract the flag.

## Background

Many teams store secrets as [CI/CD variables](https://docs.gitlab.com/ci/variables/). Misconfigured jobs or verbose logging can leak these values if access control and masking is not properly set up.

## Scenario Description

### Prepare the Tooling

From the lab root, run: `make shell` This opens a shell in the pentester container.

Then  create a new  Personal Access Token in the GitLab UI: 
1. Go to http://localhost > User menu > Settings > Access Tokens
2. Set the Scopes: api, read_api, read_repository
3. Then add the created token to under the `token` key in the Pipeleek config file `~/.config/pipeleek/pipeleek.yaml`

```bash
# edit the config file
vim ~/.config/pipeleek/pipeleek.yaml

# Modify the content and add the PAT you've generated before
gitlab:
  url: http://gitlab
  token: glpat-3qXyv3VI_nWJ8uin5ucy6m86MQp1OjIH.01.[example]

# Test its working
pipeleek enum
```

### Find the Flag

[Pipeleek](https://github.com/CompassSecurity/pipeleek) is a tool which can be used to search for secrets in CI/CD pipeline logs in an automated way. We can use it to find the flag hidden in some job output log.


> Pipleek does not detect the flag format as secret by default, therefore we need to add a custom role to our Pipeleek secret rules configuration.

Add the new custom rule to the `rules.yml` file
```bash
# run the tool first so it will populate the rules.yml intially
pipeleek scan

# Add the new rule to the now existing file
cat <<'EOF' >> rules.yml
  - pattern:
      name: Lab Flag
      regex: 'flag\{[^}]+\}'
      confidence: high
EOF
```

At this point we can start our first scan with the most basic configuration available.
```bash
pipeleek scan
```

Review the output, find the flag and submit it.
