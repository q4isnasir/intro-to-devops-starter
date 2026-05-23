# --- Application Load Balancer ---
# Public-facing entry point. Lives in both public subnets for high availability.
resource "aws_lb" "main" {
  name               = "fruitapi-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  tags = {
    Name = "fruitapi-alb"
  }
}

# --- Target Group ---
# Where ECS tasks register themselves. ALB forwards traffic here.
# target_type = "ip" is required for Fargate (tasks don't have EC2 instance IDs).
resource "aws_lb_target_group" "fruitapi" {
  name        = "fruitapi-tg"
  port        = var.app_port
  protocol    = "HTTP"
  target_type = "ip"
  vpc_id      = aws_vpc.main.id

  health_check {
    enabled             = true
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    Name = "fruitapi-tg"
  }
}

# --- Listener ---
# Accepts HTTP traffic on port 80 and forwards it to the target group.
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.fruitapi.arn
  }

  tags = {
    Name = "fruitapi-listener"
  }
}
