from server.graders.k8s_grader import grade_task5

# Test 1: Only fix replicas
config1 = """apiVersion: apps/v1
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
            - containerPort: "80"
          resources:
            limits:
              cpu: "500"
"""

reward1, msg1, fixed1 = grade_task5(config1)
print(f'Step 1 (replicas fixed): Reward={reward1}, Fixed={fixed1}')
print(f'  Error: {msg1}\n')

# Test 2: Fix replicas + port
config2 = """apiVersion: apps/v1
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
              cpu: "500"
"""

reward2, msg2, fixed2 = grade_task5(config2)
print(f'Step 2 (replicas + port fixed): Reward={reward2}, Fixed={fixed2}')
print(f'  Error: {msg2}\n')

# Test 3: Fix everything
config3 = """apiVersion: apps/v1
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

reward3, msg3, fixed3 = grade_task5(config3)
print(f'Step 3 (all fixed): Reward={reward3}, Fixed={fixed3}')
print(f'  Message: {msg3}')
