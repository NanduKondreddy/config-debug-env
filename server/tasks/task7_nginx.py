TASK_ID = "task7_nginx"
DIFFICULTY = "very_hard"
FILE_TYPE = "nginx"
NUM_BUGS = 3

DESCRIPTION = (
    "An nginx reverse proxy configuration with multi-step bugs. "
    "Requires fixing syntax (semicolons), directives (protocol), and routing logic (headers)."
)

# Bug 1 (Syntax): Missing semicolons in listen, error_log, and proxy_pass directives
# Bug 2 (Protocol): proxy_pass for / missing http:// protocol prefix
# Bug 3 (Routing): API endpoint missing headers
BROKEN_CONFIG = """events {}

http {
    server {
        listen 80

        location / {
            proxy_pass localhost:3000
        }

        location /api/ {
            proxy_pass http://localhost:5000
        }

        error_log logs/error.log
    }
}"""

ERROR_MESSAGE = (
    "nginx configuration has syntax, directive, and routing errors: "
    "missing semicolons, missing http:// prefix in proxy_pass, and missing required headers in API routing."
)

GROUND_TRUTH = """events {}

http {
    server {
        listen 80;

        location / {
            proxy_pass http://localhost:3000;
        }

        location /api/ {
            proxy_pass http://localhost:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        error_log logs/error.log;
    }
}"""
