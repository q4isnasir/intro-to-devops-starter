resource "aws_cloudwatch_log_group" "fruitapi" {
  name              = "/ecs/fruitapi"
  retention_in_days = 7 # logs auto-deleted after 7 days to control cost

  tags = {
    Name = "fruitapi-logs"
  }
}
