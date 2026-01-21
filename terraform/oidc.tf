provider "aws" {
  region = "us-east-1"
}

# 1️⃣ Create OIDC provider for GitHub Actions
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
  
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"] # GitHub default thumbprint
}

# 2️⃣ Create IAM Role for GitHub Actions
resource "aws_iam_role" "github_actions_role" {
  name = "github-actions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
             StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:joyboy2701/ecs-python-app:*"
          }
        }
      }
    ]
  })
}

# 3️⃣ Attach Policy (ECR push & ECS deploy example)
resource "aws_iam_policy" "github_actions_policy" {
  name        = "GitHubActionsPolicy"
  description = "Permissions for GitHub Actions to push Docker images and manage ECS"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchCheckLayerAvailability",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
          "ecs:UpdateService",
          "ecs:DescribeServices",
          "ecs:DescribeTaskDefinition",
          "ecs:RegisterTaskDefinition"
        ]
        Resource = "*"
      }
    ]
  })
}

# 4️⃣ Attach Policy to Role
resource "aws_iam_role_policy_attachment" "attach_policy" {
  role       = aws_iam_role.github_actions_role.name
  policy_arn = aws_iam_policy.github_actions_policy.arn
}
