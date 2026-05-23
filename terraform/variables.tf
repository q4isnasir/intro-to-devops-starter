# Inputs to the Terraform config. Override with -var or terraform.tfvars

variable "image_name" {
  description = "Docker image name - FruitAPI (no tag)."
  type        = string
  default     = "ghcr.io/q4isnasir/intro-to-devops-starter"
}

variable "image_tag" {
  description = "Tag of the FruitAPI image to run."
  type        = string
  default     = "latest"
}

variable "app_port" {
  description = "Host port to expose the FruitAPI on."
  type        = number
  default     = 8000
}

variable "mysql_database" {
  description = "Name of the MySQL database to create."
  type        = string
  default     = "fruitdb"
}

variable "mysql_user" {
  description = "MySQL non-root user the app will use."
  type        = string
  default     = "fruituser"
}

variable "mysql_password" {
  description = "MySQL password for the app user. NEVER hardcode for production."
  type        = string
  default     = "fruitpass"
  sensitive   = true
}

variable "mysql_root_password" {
  description = "MySQL root password. NEVER hardcode for production."
  type        = string
  default     = "rootpassword"
  sensitive   = true
}
