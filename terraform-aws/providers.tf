provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "intro-to-devops"
      ManagedBy   = "terraform"
      Environment = "dev"
    }
  }
}
