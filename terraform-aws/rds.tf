# DB subnet group — RDS requires subnets in 2+ AZs.
resource "aws_db_subnet_group" "main" {
  name       = "fruitapi-db-subnet-group"
  subnet_ids = aws_subnet.public[*].id

  tags = {
    Name = "fruitapi-db-subnet-group"
  }
}

# The RDS MySQL instance.
resource "aws_db_instance" "main" {
  identifier     = "fruitapi-db"
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class

  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = var.db_allocated_storage # disable autoscaling for predictable cost
  storage_type          = "gp2"
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  # Course/dev settings — would be different in production:
  publicly_accessible        = true  # so you can connect from your laptop for debugging
  skip_final_snapshot        = true  # don't snapshot on destroy (faster teardown)
  deletion_protection        = false # allow terraform destroy to work
  backup_retention_period    = 0     # daily backups for 7 days (lecture 5 requirement, default behaviour)
  auto_minor_version_upgrade = true

  tags = {
    Name = "fruitapi-db"
  }
}
