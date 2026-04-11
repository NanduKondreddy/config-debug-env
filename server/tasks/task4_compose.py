TASK_ID = "task4_compose"
DIFFICULTY = "medium"
FILE_TYPE = "docker-compose"
NUM_BUGS = 4

DESCRIPTION = (
    "A docker-compose.yml file for a multi-service application with a web frontend "
    "(Node.js app running on port 3000), a PostgreSQL database, and a Redis cache. "
    "Services should be connected via a custom network and the web service should "
    "depend on the database and cache services."
)

# Bug 1 (Syntax): Wrong indentation on volumes key
# Bug 2 (Semantic): Service references non-existent network name
# Bug 3 (Runtime): Port mapping "8080:80" should be "8080:3000" (app runs on 3000)
# Bug 4 (Integration): depends_on references "postgres" but service is defined as "db"
BROKEN_CONFIG = """version: "3.8"

services:
  web:
    build: ./app
    ports:
      - "8080:80"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://cache:6379
    depends_on:
      - postgres
      - cache
    networks:
      - frontend-net

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=mydb
  volumes:
      - db-data:/var/lib/postgresql/data
    networks:
      - backend-net

  cache:
    image: redis:7-alpine
    networks:
      - backend-net

networks:
  app-network:
    driver: bridge

volumes:
  db-data:"""

ERROR_MESSAGE = (
    "docker-compose config error: yaml parse error near 'volumes' key. "
    "Additionally, there are issues with service references, network names, "
    "and port mappings that need to be fixed."
)

GROUND_TRUTH = """version: "3.8"

services:
  web:
    build: ./app
    ports:
      - "8080:3000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
      - REDIS_URL=redis://cache:6379
    depends_on:
      - db
      - cache
    networks:
      - app-network

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=mydb
    volumes:
      - db-data:/var/lib/postgresql/data
    networks:
      - app-network

  cache:
    image: redis:7-alpine
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  db-data:"""
