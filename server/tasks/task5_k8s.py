TASK_ID = "task5_k8s"
DIFFICULTY = "hard"
FILE_TYPE = "kubernetes"
NUM_BUGS = 3

DESCRIPTION = (
    "A Kubernetes Deployment manifest with multi-step bugs. Requires fixing replicas type, "
    "containerPort type, and CPU resource units. Each fix provides intermediate feedback."
)

# Bug 1 (Type): replicas = "three" (string, should be integer)
# Bug 2 (Type): containerPort = "80" (string, should be integer)
# Bug 3 (Domain): cpu = "500" (missing 'm' suffix, should be "500m")
BROKEN_CONFIG = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: "three"
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-container
          image: nginx
          ports:
            - containerPort: "80"
          resources:
            limits:
              cpu: "500"
"""

ERROR_MESSAGE = (
    "Kubernetes manifest has type and unit errors: replicas must be integer, "
    "containerPort must be integer, and cpu must include millicores unit (e.g., 500m)."
)

GROUND_TRUTH = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: my-container
          image: nginx
          ports:
            - containerPort: 80
          resources:
            limits:
              cpu: "500m"
"""

