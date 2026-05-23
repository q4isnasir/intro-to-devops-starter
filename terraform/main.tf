# Local Docker setup that recreates the setup we previously built manually:
# - one MySQL 8 container for the database
# - one FruitAPI container using our GHCR image and connecting to MySQL
#
# Useful commands:
#   terraform init     (run once to set things up)
#   terraform plan     (preview the changes)
#   terraform apply    (create the containers)
#   terraform destroy  (remove everything)

# ---------------------------------------------------------------------------
# Create a private Docker bridge network so both containers can communicate
# using container names, such as "fruitapi-mysql", instead of IP addresses.
# For local Docker, this plays a similar role to a subnet inside an AWS VPC.
# ---------------------------------------------------------------------------

resource "docker_network" "fruitapi_net" {
  name = "fruitapi-network"
}

# ---------------------------------------------------------------------------
# MySQL image and container
# ---------------------------------------------------------------------------

# Ask Terraform to download the mysql:8.0 image if it is not already available locally.
resource "docker_image" "mysql" {
  name         = "mysql:8.0"
  keep_locally = true  # keep the image even after running `terraform destroy`
}

resource "docker_container" "mysql" {
  name  = "fruitapi-mysql"
  image = docker_image.mysql.image_id

  # These environment variables are used by the official MySQL image
  # when the container starts for the first time. They create the database
  # and set up the non-root user.
  env = [
    "MYSQL_ROOT_PASSWORD=${var.mysql_root_password}",
    "MYSQL_DATABASE=${var.mysql_database}",
    "MYSQL_USER=${var.mysql_user}",
    "MYSQL_PASSWORD=${var.mysql_password}",
  ]

  # Map MySQL's port to the Mac as well, so we can connect to it directly
  # for debugging if needed, for example using a local mysql client.
  ports {
    internal = 3306
    external = 3306
  }

  # Add the MySQL container to the shared Docker network so FruitAPI can
  # reach it using the alias "mysql".
  networks_advanced {
    name    = docker_network.fruitapi_net.name
    aliases = ["mysql"]
  }

  restart = "unless-stopped"
}

# ---------------------------------------------------------------------------
# FruitAPI image and container
# ---------------------------------------------------------------------------

# Pull the FruitAPI image from GHCR. The image tag is defined in variables.tf.
resource "docker_image" "fruitapi" {
  name         = "${var.image_name}:${var.image_tag}"
  keep_locally = true
}

resource "docker_container" "fruitapi" {
  name  = "fruitapi"
  image = docker_image.fruitapi.image_id

  # DB_HOST uses the MySQL container's network alias.
  # Because both containers are on the same Docker network, FruitAPI can
  # talk to MySQL by name instead of relying on localhost or manual IPs.
  env = [
    "DB_HOST=mysql",
    "DB_PORT=3306",
    "DB_USER=${var.mysql_user}",
    "DB_PASSWORD=${var.mysql_password}",
    "DB_NAME=${var.mysql_database}",
  ]

  ports {
    internal = 8000
    external = var.app_port
  }

  networks_advanced {
    name = docker_network.fruitapi_net.name
  }

  # Start the MySQL container before starting FruitAPI.
  # This only guarantees that the MySQL container exists, not that MySQL is
  # fully ready yet. The app startup logic and SQLAlchemy connection handling
  # can deal with a short MySQL warmup period.
  depends_on = [docker_container.mysql]

  restart = "unless-stopped"
}
