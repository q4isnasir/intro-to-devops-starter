# --- ECS Cluster ---
# A logical grouping for ECS services. Free resource.
resource "aws_ecs_cluster" "main" {
  name = "fruitapi-cluster"

  tags = {
    Name = "fruitapi-cluster"
  }
}

# --- ECS Task Definition ---
# The blueprint: image, env vars, secrets injection, ports, sizing.
resource "aws_ecs_task_definition" "fruitapi" {
  family                   = "fruitapi"
  network_mode             = "awsvpc" # required for Fargate
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.task_cpu
  memory                   = var.task_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "fruitapi"
      image     = var.container_image
      essential = true

      portMappings = [
        {
          containerPort = var.app_port
          hostPort      = var.app_port
          protocol      = "tcp"
        }
      ]

      # Non-sensitive env vars
      environment = [
        { name = "DB_HOST", value = aws_db_instance.main.address },
        { name = "DB_PORT", value = tostring(aws_db_instance.main.port) },
        { name = "DB_NAME", value = var.db_name },
      ]

      # Sensitive values — injected from Secrets Manager at runtime.
      # Format: secret_arn:json-key:: (the :: at the end is required syntax)
      secrets = [
        {
          name      = "DB_USER"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:username::"
        },
        {
          name      = "DB_PASSWORD"
          valueFrom = "${aws_secretsmanager_secret.db_credentials.arn}:password::"
        },
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.fruitapi.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])

  tags = {
    Name = "fruitapi-task"
  }
}

# --- ECS Service ---
# Keeps `desired_count` copies of the task running.
# In Lecture 4 this serves traffic directly via public IP.
# In Lecture 5 we'll add an ALB and register tasks to a target group.
resource "aws_ecs_service" "fruitapi" {
  name            = "fruitapi-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.fruitapi.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = true # so tasks can pull image + connect to DB without NAT
  }

  # Wait for RDS to be available before starting the service.
  depends_on = [aws_db_instance.main]

  tags = {
    Name = "fruitapi-service"
  }
}
