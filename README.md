# intro-to-devops-app

This is my homework repository for the Intro to DevOps course.

The project starts with a small FastAPI application, and then gets extended step by step during the course. Across the lectures, the app is updated with more endpoints, a database, tests, Docker, CI/CD, AWS deployment, and security-related improvements.

**Start here:** [PROJECT-REQUIREMENTS.md](./PROJECT-REQUIREMENTS.md)  
This file explains what the app needs to do and how the requirements connect to the course tasks.

---

## What this project is about

FruitAPI is a small REST API for managing a list of fruits.

The main goal of this project is not just the API itself, but using it to practise DevOps concepts in a realistic way. During the course, the app is used to learn things like Docker, automated testing, infrastructure as code, AWS deployment, logging, and continuous deployment.

Main technologies used:

- **Backend:** Python 3.12, FastAPI, Uvicorn
- **Database:** MySQL 8 using SQLAlchemy and PyMySQL
- **Containerisation:** Docker with a multi-stage Dockerfile based on `python:3.12-slim`
- **Cloud deployment:** AWS in `eu-north-1`
  - VPC
  - RDS
  - ECS Fargate
  - Application Load Balancer
  - Secrets Manager
  - CloudWatch
- **CI/CD:** GitHub Actions and GHCR for storing Docker images

---

## Architecture in production

In the AWS production setup, the app is accessed through a public Application Load Balancer on port 80. The load balancer checks the `/health` endpoint to make sure the app is alive, and then forwards traffic to the healthy ECS Fargate tasks running the FruitAPI container. The service runs with two tasks, so if one task has a problem, the other one can still handle requests.

Each ECS task connects to an RDS MySQL database, which stores the fruit data. The database username and password are stored in AWS Secrets Manager instead of being written in the code or committed to GitHub. When the ECS task starts, those values are passed into the container as environment variables.

The app logs are sent to CloudWatch in the log group `/ecs/fruitapi`. This makes it easier to check what the running containers are doing.

All AWS infrastructure is written in Terraform inside the `terraform-aws/` folder. I did not create the main infrastructure manually through the AWS Console.

/

---

## How to run locally

The easiest way to run the app locally is with Docker. The app also needs a MySQL 8 database that it can connect to. This can be MySQL running on the laptop, or MySQL running in another Docker container.

```bash
# build the Docker image
docker build -t fruitapi:dev .

# run the app container and connect it to MySQL
docker run --rm -p 8000:8000 \
  -e DB_HOST=host.docker.internal \
  -e DB_PORT=3306 \
  -e DB_USER=fruituser \
  -e DB_PASSWORD=fruitpass \
  -e DB_NAME=fruitdb \
  fruitapi:dev

# quick check that the app is running
curl http://localhost:8000/health
curl http://localhost:8000/fruits
```

To run the tests:

```bash
# unit tests: these are fast and do not need MySQL
# they use the in-memory fake store
pytest app/ -v

# integration tests: these need the API to already be running
BASE_URL=http://localhost:8000 pytest tests/ -v
```

---

## How CI/CD works

This project uses two GitHub Actions workflows. The branching style is GitHub Flow, so changes are made in a feature branch, opened as a pull request, checked by CI, and then merged into `main`.

### `pr.yml` — pull request workflow

This workflow runs when a pull request is opened or updated.

It runs the unit tests only, because those are quick and give fast feedback while working on the PR. The `unit-tests` check is required by branch protection, so the PR cannot be merged unless the tests pass.

### `main.yml` — main branch workflow

This workflow runs after a pull request is merged into `main`.

It has three jobs:

1. **`unit-tests`**  
   Runs the unit tests again on the final merged version of the code.

2. **`build-and-push`**  
   Starts a real MySQL service, builds the Docker image, runs the integration tests against the running container, and then pushes the image to GHCR. The image is pushed with two tags: `:latest` and the commit SHA.

3. **`deploy`**  
   This is the continuous deployment part. It uses AWS credentials stored as GitHub repository secrets, then runs `aws ecs update-service --force-new-deployment`. This tells ECS to start a new rolling deployment using the latest image. After that, it waits with `aws ecs wait services-stable`, so the workflow only passes if the ECS service becomes stable again.

### Zero-downtime deploys

The ECS service uses:

```hcl
deployment_minimum_healthy_percent = 100
deployment_maximum_percent         = 200
```

This means ECS keeps the old tasks running while it starts the new ones. Once the new tasks are healthy, ECS can remove the old ones. Together with two replicas and the ALB health check on `/health`, this allows the app to keep responding during deployment.

### Secrets

The AWS credentials are stored as GitHub Actions repository secrets:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

They are passed into the deploy job at runtime by the official AWS credentials action. They are also hidden in the workflow logs and are not stored in the repository.

---

## Branching strategy — GitHub Flow

I chose **GitHub Flow** for this project.

The main reason is that this is a small project, and I am working on it alone. A more complicated branching model, like git-flow, would add extra branches without really helping much.

With GitHub Flow:

- work is done in short feature branches
- each change goes through a pull request
- CI runs before merging
- `main` should always stay deployable
- every merge to `main` can trigger the deployment workflow

The `main` branch is protected:

- changes must go through a pull request
- the `unit-tests` check must pass before merging

---

## Deploying the AWS stack

The AWS infrastructure is inside the `terraform-aws/` folder. The IAM user `terraform-devops` is used for local Terraform commands and also for the GitHub Actions deploy job.

```bash
cd terraform-aws
terraform init
terraform plan -out=plan.tfplan
terraform apply plan.tfplan

# use the alb_url output to test the API

terraform destroy   # destroy the stack after testing
```

The stack costs around $0.05 per hour while it is running because it uses an ALB, RDS, and two Fargate tasks. It is only meant to be used for testing, so the normal workflow is: apply, test, then destroy.
