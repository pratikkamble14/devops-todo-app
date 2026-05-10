FROM python:3.12-slim

LABEL maintainer="kamblepratik1404@gmail.com"
LABEL description="DevOps Todo Application"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY tests/ ./tests/

# Create directory for SQLite database persistence
RUN mkdir -p /app/instance
RUN mkdir -p /app/data

EXPOSE 5000

ENV FLASK_APP=app/app.py
ENV PYTHONUNBUFFERED=1

# Volume for SQLite database persistence
VOLUME ["/app/instance"]

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

CMD ["python", "app/app.py"]
