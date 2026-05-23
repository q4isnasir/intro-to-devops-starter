# Generate a strong random password for the RDS master user.
# RDS doesn't allow these chars in the password: / @ " (space)
resource "random_password" "db_password" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

# Create the secret in AWS Secrets Manager.
resource "aws_secretsmanager_secret" "db_credentials" {
  name                    = "fruitapi/db-credentials"
  description             = "RDS MySQL master credentials for FruitAPI"
  recovery_window_in_days = 0 # 0 = delete immediately on destroy (course-friendly; prod would be 7-30)

  tags = {
    Name = "fruitapi-db-credentials"
  }
}

# Store the actual credential values as a JSON blob in that secret.
resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
    dbname   = var.db_name
  })
}
