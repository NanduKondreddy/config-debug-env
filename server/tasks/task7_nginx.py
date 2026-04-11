TASK_ID = "task7_nginx"
DIFFICULTY = "very_hard"
FILE_TYPE = "nginx"
NUM_BUGS = 3

DESCRIPTION = (
    "An nginx reverse proxy configuration with multi-step bugs. "
    "Requires fixing syntax (semicolons), directives (protocol), and routing logic (headers)."
)

# Bug 1 (Syntax): Missing semicolons in listen and error_log directives
# Bug 2 (Directive): proxy_pass missing http:// protocol prefix
# Bug 3 (Logic): Improper routing with missing headers for API endpoint
BROKEN_CONFIG = """events {}

http {
    server {
        listen 80

        location / {
            proxy_pass localhost:3000
        }

        location /api {
            proxy_pass http://localhost:5000
            proxy_set_header Host $host
            proxy_set_header X-Real-IP $remote_addr
        }

        error_log logs/error.log
    }
}"""

ERROR_MESSAGE = (
    "nginx configuration has syntax, directive, and routing errors: "
    "missing semicolons, missing http:// prefix in proxy_pass, and improper API routing."
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
