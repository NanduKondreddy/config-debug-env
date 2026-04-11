TASK_ID = "task1_json"
DIFFICULTY = "easy"
FILE_TYPE = "json"
NUM_BUGS = 2

DESCRIPTION = (
    "A simple application configuration file in JSON format. "
    "It should define the app name, port (as integer), host, and debug mode."
)

# The broken config (what the agent sees)
# Bug 1 (Syntax): Missing comma after "my-service"
# Bug 2 (Semantic): port is string "8080" instead of integer 8080
BROKEN_CONFIG = """{
    "app_name": "my-service"
    "port": "8080",
    "host": "0.0.0.0",
    "debug": true
}"""

ERROR_MESSAGE = (
    "JSON parse error: Expecting ',' delimiter: line 3 column 5 (char 33). "
    "Additionally, there may be type issues with some fields."
)

GROUND_TRUTH = """{
    "app_name": "my-service",
    "port": 8080,
    "host": "0.0.0.0",
    "debug": true
}"""
