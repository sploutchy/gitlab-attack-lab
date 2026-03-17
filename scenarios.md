# Scenario 0 - Intro

Login and find demo flag.
Go to security-team/security-tool there find the welcome flag.

# Scenario 1 - CICD Leaks

Find with scan a glpat -> fetch flag from other project variables where access level is 50.
dump the variables of the other project where access level is already 30 using a change on repo.
Artifact secret flag and .dotenv secret in the same


# Scenario 3 - Renovate Hijacker

Create a renovate exploit repo
Find the renovate bot by username
extract its token
find the flag in another private repo renovated by renovate

# Scenario 4 - Abuse Renovate Privesc

identify protected flag is in ci/cd only on main, youre dev
A renovate bot is on the orject with maintainer
Exploit it and inject a malicous ci/cd

# Scenario 5 - Runner Abuse

Identify the shared runner.
Break out of the runner
Extract others jobs token and find the flag in there.

# Scenario 2 - Artipacked CI/CD token leak

identify the container build repo
extract the token
use it to dump the ci/cd variables
