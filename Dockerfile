FROM python:3.11-slim

WORKDIR /app

# install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy project
COPY app ./app
COPY db  ./db
COPY tests ./tests
COPY scripts ./scripts

# runtime environment variables
ENV DATABASE_URL=""
ENV GOOGLE_API_KEY=""
ENV USE_AI_STUB="true"

# make entrypoint executable
RUN chmod +x scripts/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/scripts/entrypoint.sh"]

# Local Postgres (Docker)
# docker-compose up --build

# Cloud Postgres (Aiven)
# docker build -t sprintsync-app . && docker run -it --rm -p 8000:8000 --env-file .env sprintsync-app
