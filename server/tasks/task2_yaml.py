TASK_ID = "task2_yaml"
DIFFICULTY = "easy"
FILE_TYPE = "yaml"
NUM_BUGS = 2

DESCRIPTION = (
    "A service configuration file in YAML format. "
    "It should define the service name, version, port, host, database settings, "
    "and logging configuration with proper indentation and all required fields."
)

# The broken config (what the agent sees)
# Bug 1 (Syntax): Wrong indentation on nested key (3 spaces instead of 2)
# Bug 2 (Semantic): Missing required field "version"
BROKEN_CONFIG = """service:
  name: my-service
  port: 8080
  host: 0.0.0.0
  database:
     host: localhost
     port: 5432
   name: mydb
  logging:
    level: info
    format: json"""

ERROR_MESSAGE = (
    "YAML parse error: mapping values are not allowed in this context. "
    "Additionally, the configuration may be missing required fields."
)

GROUND_TRUTH = """service:
  name: my-service
  version: "1.0.0"
  port: 8080
  host: 0.0.0.0
  database:
    host: localhost
    port: 5432
    name: mydb
  logging:
    level: info
    format: json"""
