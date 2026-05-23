variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-north-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for the public subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "availability_zones" {
  description = "Availability zones to deploy subnets into"
  type        = list(string)
  default     = ["eu-north-1a", "eu-north-1b"]
}

variable "my_ip" {
  description = "Your public IP in CIDR notation for direct access to ALB and RDS (for course/debug)"
  type        = string
  default     = "205.164.155.98/32"
}

variable "app_port" {
  description = "Port the FruitAPI listens on inside the container"
  type        = number
  default     = 8000
}

variable "db_name" {
  description = "Name of the MySQL database"
  type        = string
  default     = "fruitdb"
}

variable "db_username" {
  description = "Master username for the MySQL database"
  type        = string
  default     = "fruitadmin"
}

variable "db_instance_class" {
  description = "RDS instance size (db.t3.micro is free tier eligible)"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB (20 is the free tier max)"
  type        = number
  default     = 20
}
