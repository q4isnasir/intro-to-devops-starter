# --- ALB Security Group ---
# Allows HTTP from anywhere (this is the public-facing entry point).
resource "aws_security_group" "alb" {
  name        = "fruitapi-alb-sg"
  description = "Allow HTTP traffic to the ALB"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "fruitapi-alb-sg"
  }
}

# --- ECS Task Security Group ---
# Allows app port ONLY from the ALB SG (no direct internet access to tasks).
# Also allows your laptop IP for debugging before the ALB is set up.
resource "aws_security_group" "ecs_tasks" {
  name        = "fruitapi-ecs-tasks-sg"
  description = "Allow app traffic from the ALB and your IP"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "App port from ALB"
    from_port       = var.app_port
    to_port         = var.app_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  ingress {
    description = "App port from my IP (debug)"
    from_port   = var.app_port
    to_port     = var.app_port
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "fruitapi-ecs-tasks-sg"
  }
}

# --- RDS Security Group ---
# Allows MySQL ONLY from the ECS task SG and your laptop IP. Never from the internet.
resource "aws_security_group" "rds" {
  name        = "fruitapi-rds-sg"
  description = "Allow MySQL from ECS tasks and my IP"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "MySQL from ECS tasks"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs_tasks.id]
  }

  ingress {
    description = "MySQL from my IP (debug)"
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    cidr_blocks = [var.my_ip]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "fruitapi-rds-sg"
  }
}
