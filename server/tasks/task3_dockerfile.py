TASK_ID = "task3_dockerfile"
DIFFICULTY = "medium"
FILE_TYPE = "dockerfile"
NUM_BUGS = 3

DESCRIPTION = (
    "A Dockerfile for a Python web application. It should use the python:3.9-slim "
    "base image, install dependencies from requirements.txt, copy the application code, "
    "expose port 8000, and run the application with uvicorn."
)

# Bug 1 (Syntax): Wrong escape character for multi-line RUN (using ^ instead of \)
# Bug 2 (Semantic): Wrong base image tag (python:3.9-slm instead of python:3.9-slim)
# Bug 3 (Runtime): Missing EXPOSE directive for the application port
BROKEN_CONFIG = """FROM python:3.9-slm

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt ^
    && pip install uvicorn

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]"""

ERROR_MESSAGE = (
    "Dockerfile build error: failed to resolve base image 'python:3.9-slm'. "
    "Additionally, the RUN command may have syntax issues with multi-line continuation, "
    "and the container may not be accessible on the expected port."
)

GROUND_TRUTH = """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt \\
    && pip install uvicorn

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]"""
