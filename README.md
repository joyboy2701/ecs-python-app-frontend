# Python App Frontend – CI/CD with GitHub Actions, ECR, and ECS

This repository contains a Python-based application packaged as a Docker image and deployed automatically to **AWS ECS** using **GitHub Actions**. The CI/CD pipeline is triggered when a Pull Request (PR) to the `master` branch is **approved, merged, and closed**.

---

## 📁 Project Structure

```
.
├── api
│   ├── app.py          # Application source code
│   └── Dockerfile      # Docker image definition
└── .github
    └── workflows
        └── cicd.yml    # GitHub Actions CI/CD pipeline
```

---

## 🚀 What This Pipeline Does

The GitHub Actions workflow automates the following steps:

1. **Triggers only when a PR is merged into `master`**
2. **Builds a Docker image** from the `api/` directory
3. **Pushes the image to Amazon ECR**
4. **Forces a new deployment on Amazon ECS**, so the service pulls the latest image

This provides a fully automated deployment flow from code merge → production update.

---

## 🔁 CI/CD Workflow Trigger

The pipeline is triggered by this event:

```yaml
on:
  pull_request:
    types: [closed]
    branches:
      - master
```

And it only runs **if the PR was actually merged**:

```yaml
if: github.event.pull_request.merged == true
```

This ensures:
- ❌ No pipeline runs on PR close without merge
- ✅ Pipeline runs only after approved & merged code

---

## 🔐 Authentication (OIDC)

The pipeline uses **GitHub OIDC (OpenID Connect)** to securely assume an AWS IAM role.

No long-lived AWS access keys are stored in GitHub.

Required GitHub Secrets:

| Secret Name | Description |
|------------|------------|
| `AWS_ROLE_ARN` | IAM Role assumed by GitHub Actions |
| `REGION` | AWS region (e.g. `us-east-1`) |
| `ECR_REGISTRY` | ECR registry URL (e.g. `123456789012.dkr.ecr.us-east-1.amazonaws.com`) |

---

## 🐳 Docker Build & Push (ECR)

The pipeline builds the Docker image using the `api/Dockerfile`:

```bash
docker build -t upload-api:latest ./api
```

It then tags and pushes the image to Amazon ECR:

```bash
docker tag upload-api:latest <ECR_REGISTRY>/upload-api:latest
docker push <ECR_REGISTRY>/upload-api:latest
```

This updates the `latest` image in ECR.

---

## ☁️ ECS Deployment

After pushing the image, the pipeline forces a new deployment on ECS:

```bash
aws ecs update-service \
  --cluster api-service \
  --service api-service \
  --force-new-deployment
```

This causes ECS to:
- Pull the latest image from ECR
- Restart tasks
- Deploy the updated application automatically

---

## 🧩 Complete CI/CD Flow

1. Create a **new feature branch** from `master`
2. Make code changes
3. Commit & push the branch
4. Open a **Pull Request to `master`**
5. PR is **reviewed and approved**
6. PR is **merged manually**
7. GitHub Actions pipeline runs automatically
8. Docker image is built & pushed to ECR
9. ECS service is updated with the new image

---

## ✅ Benefits of This Setup

- Fully automated deployments
- Secure AWS authentication (OIDC)
- No manual Docker or ECS steps
- Controlled deployments via PR approvals
- Production updates only on merged code

---

## 📌 Notes

- Ensure the ECS service is configured to use the `latest` image tag
- IAM role must have permissions for:
  - ECR (push images)
  - ECS (update service)
- This pipeline assumes **ECR repositories already exist**

---
