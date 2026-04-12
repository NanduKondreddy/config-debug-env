TASK_ID = "task1_json"
DIFFICULTY = "medium"
FILE_TYPE = "json"
NUM_BUGS = 3

DESCRIPTION = (
    "A microservice configuration file in JSON format. "
    "It defines app metadata, networking, environment variables, and volume mounts. "
    "This is a realistic scenario where multiple interdependent fixes are needed."
)

# The broken config (what the agent sees)
# Bug 1 (Syntax): Missing comma after "my-service"
# Bug 2 (Structural): env values missing quotes (should be strings, not bare values)
# Bug 3 (Semantic): volumes should be object mapping, not array
BROKEN_CONFIG = """{
    "app_name": "my-service"
    "port": 8080,
    "host": "0.0.0.0",
    "debug": true,
    "env": [
        "LOG_LEVEL=info",
        "DB_HOST=localhost",
        "PORT=8080"
    ],
    "volumes": [
        "/data:/data",
        "/logs:/logs"
    ]
}"""

ERROR_MESSAGE = (
    "JSON parse error: Expecting ',' delimiter after app_name. "
    "Additionally, 'env' values are unquoted strings (should be quoted), "
    "and 'volumes' is an array instead of an object mapping."
)

GROUND_TRUTH = """{
    "app_name": "my-service",
    "port": 8080,
    "host": "0.0.0.0",
    "debug": true,
    "env": {
        "LOG_LEVEL": "info",
        "DB_HOST": "localhost",
        "PORT": "8080"
    },
    "volumes": {
        "data": "/data:/data",
        "logs": "/logs:/logs"
    }
}"""
