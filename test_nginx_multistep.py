from server.graders.nginx_grader import grade_task7

# Test 1: Only fix syntax (listen and error_log semicolons)
config1 = """events {}

http {
    server {
        listen 80;

        location / {
            proxy_pass localhost:3000
        }

        location /api {
            proxy_pass http://localhost:5000
        }

        error_log logs/error.log;
    }
}"""

reward1, msg1, fixed1 = grade_task7(config1)
print(f'Step 1 (syntax fixed): Reward={reward1}, Fixed={fixed1}')
print(f'  Error: {msg1}\n')

# Test 2: Fix syntax + proxy_pass (add http://)
config2 = """events {}

http {
    server {
        listen 80;

        location / {
            proxy_pass http://localhost:3000;
        }

        location /api {
            proxy_pass http://localhost:5000
        }

        error_log logs/error.log;
    }
}"""

reward2, msg2, fixed2 = grade_task7(config2)
print(f'Step 2 (syntax + proxy_pass fixed): Reward={reward2}, Fixed={fixed2}')
print(f'  Error: {msg2}\n')

# Test 3: Fix everything (add /api/ and headers)
config3 = """events {}

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

reward3, msg3, fixed3 = grade_task7(config3)
print(f'Step 3 (all fixed): Reward={reward3}, Fixed={fixed3}')
print(f'  Message: {msg3}')
