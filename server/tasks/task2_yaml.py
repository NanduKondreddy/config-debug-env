TASK_ID = "task2_yaml"
DIFFICULTY = "medium"
FILE_TYPE = "yaml"
NUM_BUGS = 3

DESCRIPTION = (
    "A CI/CD pipeline configuration in YAML format. "
    "It defines stages, environment variables, and job specifications. "
    "This is a realistic scenario from GitHub Actions / GitLab CI pipelines."
)

# The broken config (what the agent sees)
# Bug 1 (Syntax): Wrong indentation on nested key (3 spaces instead of 2)
# Bug 2 (Structural): env section is array instead of object
# Bug 3 (Semantic): Missing required 'timeout' field under jobs
BROKEN_CONFIG = """pipeline:
  name: ci-pipeline
  stages:
    - build
    - test
    - deploy
  env:
    - CI: "true"
    - REGISTRY: "docker.io"
  jobs:
     build_job:
      stage: build
      script:
        - npm install
        - npm run build
    test_job:
      stage: test
      script:
        - npm test"""

ERROR_MESSAGE = (
    "YAML parse error: mapping values are not allowed in this context (indentation issue). "
    "Additionally, 'env' is an array instead of an object, "
    "and jobs are missing 'timeout' specifications."
)

GROUND_TRUTH = """pipeline:
  name: ci-pipeline
  stages:
    - build
    - test
    - deploy
  env:
    CI: "true"
    REGISTRY: "docker.io"
  jobs:
    build_job:
      stage: build
      timeout: 3600
      script:
        - npm install
        - npm run build
    test_job:
      stage: test
      timeout: 1800
      script:
        - npm test"""
