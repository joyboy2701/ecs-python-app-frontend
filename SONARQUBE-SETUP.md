# SonarQube Cloud Integration with GitHub Actions

This README explains how SonarQube Cloud was integrated with GitHub Actions to scan code before merge and before deployment.

The goal of this setup is:

```text
Bad, vulnerable, or low-quality code should not be merged or deployed.
```

---

## 1. What is SonarQube Cloud?

SonarQube Cloud is a cloud-based static code analysis platform.

It scans source code and detects:

- Bugs
- Vulnerabilities
- Security Hotspots
- Code Smells
- Duplicated Code
- Maintainability Issues
- Reliability Issues
- Security Issues
- Quality Gate failures

It helps us find code quality and security issues early in the CI/CD process.

---

## 2. Why We Use SonarQube Cloud

We use SonarQube Cloud to:

- Automatically scan code in GitHub Actions
- Detect bugs and vulnerabilities before merge
- Block pull requests if the Quality Gate fails
- Stop deployment if the SonarQube scan fails
- Improve code quality and maintainability
- Review security-sensitive code before production

---

## 3. High-Level Flow

The complete flow is:

```text
Developer creates a feature branch
        ↓
Developer opens PR against master
        ↓
SonarQube Cloud scans the PR
        ↓
Quality Gate passes or fails
        ↓
If Quality Gate fails → PR merge is blocked
If Quality Gate passes → PR can be merged
        ↓
After PR is merged into master
        ↓
Deployment workflow starts
        ↓
SonarQube Cloud scans 
        ↓
Quality Gate passes or fails
        ↓
If Quality Gate fails → Deployment will not proceed
If Quality Gate passes → Deployment will proceed
        ↓
Docker image is built
        ↓
Image is pushed to ECR
        ↓
ECS service is updated
```

---

## 4. Prerequisites

Before starting, make sure you have:

- GitHub repository
- SonarQube Cloud account
- Admin access to GitHub repository
- SonarQube Cloud access to the GitHub repository
- AWS/ECR/ECS secrets configured if deployment is included

---

## 5. Create or Import Project in SonarQube Cloud

Login to SonarQube Cloud using GitHub.

Then follow these steps:

```text
SonarQube Cloud
→ Import project
→ Select GitHub
→ Authorize SonarQube Cloud
→ Select GitHub organization
→ Select repository
→ Create project
```

After importing the repository, SonarQube Cloud creates a project for it.

---

## 6. Get Organization Key and Project Key

After the project is created, open the project in SonarQube Cloud.

Go to:

```text
SonarQube Cloud
→ Your Organization
→ Your Project
→ Project Information
```

Copy these two values:

```properties
sonar.organization=YOUR_ORGANIZATION_KEY
sonar.projectKey=YOUR_PROJECT_KEY
```

Example:

```properties
sonar.organization=joyboy2701
sonar.projectKey=joyboy2701_ecs-python-app-frontend
```

These values are required in the `sonar-project.properties` file if you are using one.

---

## 7. Generate SonarQube Cloud Token

In SonarQube Cloud:

```text
Profile Icon
→ My Account
→ Security
→ Generate Token
```

Give the token a name, for example:

```text
github-actions-sonarqube
```

Copy the generated token.

Important:

```text
Do not commit this token in code.
Do not put it inside sonar-project.properties.
Do not put it directly inside GitHub Actions YAML.
```

The token must be stored securely in GitHub repository secrets.

---

## 8. Add SONAR_TOKEN in GitHub Repository Secrets

Go to your GitHub repository:

```text
GitHub Repository
→ Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

Add:

```text
Name: SONAR_TOKEN
Value: paste_your_sonarqube_cloud_token_here
```

The secret name must be exactly:

```text
SONAR_TOKEN
```

This token is used by GitHub Actions to authenticate with SonarQube Cloud and upload analysis results.

---

## 9. Add SonarQube Project Configuration

SonarQube Cloud needs project configuration so the scanner knows:

```text
Which SonarQube Cloud project to upload results to
Which organization the project belongs to
Which source code folder should be scanned
Which files/folders should be excluded
```

There are two ways to provide this configuration:

```text
Option 1: Use sonar-project.properties file
Option 2: Pass the same configuration directly in the GitHub Actions workflow
```

Using `sonar-project.properties` is **not mandatory**, but it is recommended because it keeps the configuration clean and separate from the pipeline YAML.

---

### Option 1: Using sonar-project.properties

Create this file in the root of the repository:

```text
sonar-project.properties
```

Example repository structure:

```text
repo-root/
├── api/
├── .github/
├── README.md
└── sonar-project.properties
```

Example configuration:

```properties
sonar.projectKey=joyboy2701_ecs-python-app-frontend
sonar.organization=joyboy2701

sonar.sources=api
sonar.exclusions=**/node_modules/**,**/dist/**,**/build/**,**/coverage/**,**/.next/**,**/.git/**,**/__pycache__/**,**/*.pyc

sonar.sourceEncoding=UTF-8
```

Update these values according to your SonarQube Cloud project:

```properties
sonar.projectKey=YOUR_PROJECT_KEY
sonar.organization=YOUR_ORGANIZATION_KEY
```

---

### Why `sonar.sources=api`?

In this project, the application code is inside the `api` folder:

```text
repo-root/
└── api/
```

So we use:

```properties
sonar.sources=api
```

If your code is inside another folder, update it.

Examples:

```properties
sonar.sources=src
```

or:

```properties
sonar.sources=.
```

---

### Option 2: Without sonar-project.properties

The `sonar-project.properties` file is optional. You can remove it and pass the same configuration directly inside the GitHub Actions workflow.

Example:

```yaml
- name: SonarQube Cloud Scan
  uses: SonarSource/sonarqube-scan-action@v7
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
  with:
    args: >
      -Dsonar.projectKey=joyboy2701_ecs-python-app-frontend
      -Dsonar.organization=joyboy2701
      -Dsonar.sources=api
      -Dsonar.exclusions=**/node_modules/**,**/dist/**,**/build/**,**/coverage/**,**/.next/**,**/.git/**,**/__pycache__/**,**/*.pyc
      -Dsonar.sourceEncoding=UTF-8
      -Dsonar.qualitygate.wait=true
```

This works the same way, but it makes the workflow file longer.

---

### Recommended Approach

For this setup, we recommend using `sonar-project.properties`.

Reason:

```text
It keeps the pipeline clean
It keeps SonarQube configuration in one place
It is easier to update later
It avoids putting too many scanner arguments in the GitHub Actions workflow
```

So the recommended structure is:

```text
sonar-project.properties = SonarQube project configuration
GitHub Actions workflow = Runs the SonarQube scan
SONAR_TOKEN = Authentication secret stored in GitHub
```

## 10. Disable Automatic Analysis in SonarQube Cloud

If GitHub Actions is used for scanning, disable SonarQube Cloud Automatic Analysis.

Go to:

```text
SonarQube Cloud
→ Project
→ Administration
→ Analysis Method
```

Disable:

```text
Automatic Analysis
```

Reason:

```text
You cannot use Automatic Analysis and CI-based analysis at the same time.
```

If both are enabled, GitHub Actions may fail with this error:

```text
You are running CI analysis while Automatic Analysis is enabled.
Please consider disabling one or the other.
```

For this setup, we use:

```text
CI-based analysis through GitHub Actions
```

---

## 11. Workflow 1: SonarQube PR Quality Gate

This workflow runs before merge when a pull request is created, updated, or reopened.

Create this file:

```text
.github/workflows/sonarqube-pr-check.yml
```

Add:

```yaml
name: SonarQube PR Quality Gate

on:
  pull_request:
    types: [opened, synchronize, reopened]
    branches:
      - master

jobs:
  sonarqube-scan:
    name: SonarQube PR Quality Gate
    runs-on: ubuntu-latest

    permissions:
      contents: read
      pull-requests: read

    steps:
      - name: Checkout repository
        uses: actions/checkout@v5
        with:
          fetch-depth: 0

      - name: SonarQube Cloud Scan
        uses: SonarSource/sonarqube-scan-action@v7
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        with:
          args: >
            -Dsonar.qualitygate.wait=true
```

This workflow runs when:

```text
PR is opened
PR receives a new commit
PR is reopened
```

It does not deploy anything. It only scans the code and checks the SonarQube Quality Gate.

---

## 12. Configure GitHub Ruleset / Branch Protection

To block PR merge until SonarQube passes, configure GitHub branch protection or a ruleset.

Go to:

```text
GitHub Repository
→ Settings
→ Rules
→ Rulesets
```

Create or edit a ruleset.

Set:

```text
Enforcement status: Active
```

Under target branches, select:

```text
Target branches
→ Add target
→ Include by pattern
→ master
```

Then enable:

```text
Require a pull request before merging
Require status checks to pass
Require branches to be up to date before merging
Block force pushes
```

Under required status checks, add:

```text
SonarQube PR Quality Gate
```

Save the ruleset.

Expected behavior:

```text
SonarQube check pending → Merge blocked
SonarQube check failed  → Merge blocked
SonarQube check passed  → Merge allowed
```

---

## 13. Where to See SonarQube Results

Go to SonarQube Cloud:

```text
SonarQube Cloud
→ Organization
→ Project
```

Check:

```text
Overview
Issues
Security Hotspots
Quality Gate
Measures
Code
```

## 14. Testing the Setup

To test the full flow:

```bash
git checkout master
git pull origin master

git checkout -b test/sonarqube-check
echo "test sonar workflow" >> README.md

git add README.md
git commit -m "Test SonarQube workflow"
git push -u origin test/sonarqube-check
```

Open a PR:

```text
base: master
compare: test/sonarqube-check
```

Then check:

```text
GitHub PR page
→ Checks
→ SonarQube PR Quality Gate
```

After it passes, merge the PR.

Then check:

```text
GitHub Actions
→ Build & Push Docker Images to ECR
```

---


## 15. Important Notes

Do not commit real secrets into code.

For testing secret detection, use fake/demo values only.

Do not store the SonarQube token in:

```text
README.md
sonar-project.properties
workflow YAML
source code
```

Always store it in:

```text
GitHub Repository Secrets
```

---

## 25. Final Setup Summary

The final setup includes:

```text
SonarQube Cloud project
SONAR_TOKEN stored in GitHub Secrets
sonar-project.properties in repo root
PR SonarQube workflow
Deployment workflow after PR merge
GitHub ruleset protecting master
SonarQube PR Quality Gate required before merge
```

Final behavior:

```text
Developer opens PR
        ↓
SonarQube scans code
        ↓
If Quality Gate fails → merge blocked
        ↓
If Quality Gate passes → merge allowed
        ↓
After merge → Docker image builds
        ↓
Image pushed to ECR
        ↓
ECS service updated
```