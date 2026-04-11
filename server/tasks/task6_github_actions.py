TASK_ID = "task6_github_actions"
DIFFICULTY = "hard"
FILE_TYPE = "github-actions"
NUM_BUGS = 5

DESCRIPTION = (
    "A GitHub Actions workflow that builds a Node.js application on push to main, "
    "runs tests, uploads a build artifact, and deploys it. It should use ubuntu-latest "
    "runner, checkout the code, setup Node.js, install deps, build, upload artifact as "
    "'build-output', and download the same artifact in the deploy job."
)

# Bug 1 (Syntax): Missing colon after "on" trigger value (push should be on:\n  push:)
# Bug 2 (Semantic): runs-on uses "ubuntu-latets" (typo, should be "ubuntu-latest")
# Bug 3 (Semantic): Step uses actions/checkout@v2 but with has invalid parameter name
# Bug 4 (Runtime): Environment variable referenced but not defined in env block
# Bug 5 (Integration): Build step artifact name "build-output" but deploy references "build-artifact"
BROKEN_CONFIG = """name: CI/CD Pipeline

on
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latets
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-deph: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test
        env:
          API_ENDPOINT: ${{ secrets.API_KEY }}

      - name: Build
        run: npm run build

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: build-artifact

      - name: Deploy
        run: echo "Deploying..."
"""

ERROR_MESSAGE = (
    "GitHub Actions workflow error: YAML parse error near 'on' key. "
    "Additionally, the runner name may have a typo, an action parameter name is invalid, "
    "environment variables may be misconfigured, and artifact names between jobs may not match."
)

GROUND_TRUTH = """name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test
        env:
          API_ENDPOINT: ${{ secrets.API_KEY }}

      - name: Build
        run: npm run build

      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Download artifact
        uses: actions/download-artifact@v4
        with:
          name: build-output

      - name: Deploy
        run: echo "Deploying..."
"""
