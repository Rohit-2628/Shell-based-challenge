FROM python:3.9-slim

WORKDIR /app

# Force the container to run as root so it can write to /tmp_sock
USER root

# Install exactly what we need
RUN pip install --no-cache-dir flask gunicorn

# Copy the server code
COPY app.py .

# Bind directly to the socket
CMD ["gunicorn", "--bind", "unix:/tmp_sock/.sys.sock", "app:app"]
