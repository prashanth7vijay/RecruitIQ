FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/dev.txt

COPY . .

EXPOSE 5000

# Was `flask run` (the single-threaded Flask dev server) until Phase 5
# — gunicorn and gevent were installed as dependencies (requirements/
# base.txt) but never actually wired into the container's entrypoint.
# Found while setting up load testing: worth catching specifically
# there, since `flask run` can't demonstrate anything about concurrent-
# request handling or horizontal scalability in the first place. See
# docs/scalability.md. --workers 4 is a starting point, not a tuned
# number — see the same doc for how to size it for real.
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
