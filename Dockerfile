FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Agregar /app al PYTHONPATH
ENV PYTHONPATH=/app

EXPOSE 8080

CMD ["python", "-c", "import sys; sys.path.insert(0, '/app'); from app import app; from gunicorn.app.wsgiapp import run; sys.argv = ['gunicorn', '--bind', '0.0.0.0:8080', '--workers', '1', '--threads', '8', 'app:app']; run()"]
