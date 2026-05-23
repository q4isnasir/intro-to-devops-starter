# --- ECS Task Execution Role ---
# Used by the ECS agent itself: pulling the container image, writing logs,
# and fetching secrets from Secrets Manager BEFORE the container starts.
data "aws_iam_policy_document" "ecs_task_execution_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution" {
  name               = "fruitapi-ecs-task-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json

  tags = {
    Name = "fruitapi-ecs-task-execution-role"
  }
}

# Attach AWS-managed policy that grants standard execution permissions
# (pull image from any container registry, write CloudWatch logs).
resource "aws_iam_role_policy_attachment" "ecs_task_execution" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Grant the execution role permission to read our specific secret.
# Scoped to ONE secret ARN — least privilege.
data "aws_iam_policy_document" "secrets_access" {
  statement {
    actions = [
      "secretsmanager:GetSecretValue",
    ]
    resources = [aws_secretsmanager_secret.db_credentials.arn]
  }
}

resource "aws_iam_policy" "secrets_access" {
  name        = "fruitapi-secrets-access"
  description = "Allow reading FruitAPI DB credentials secret"
  policy      = data.aws_iam_policy_document.secrets_access.json
}

resource "aws_iam_role_policy_attachment" "secrets_access" {
  role       = aws_iam_role.ecs_task_execution.name
  policy_arn = aws_iam_policy.secrets_access.arn
}

# --- ECS Task Role ---
# Used by your APPLICATION CODE while running, if it needs to call AWS APIs.
# FruitAPI doesn't currently call any AWS APIs, but the task definition
# requires this field, so we create a minimal role with no policies attached.
resource "aws_iam_role" "ecs_task" {
  name               = "fruitapi-ecs-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_assume_role.json

  tags = {
    Name = "fruitapi-ecs-task-role"
  }
}
