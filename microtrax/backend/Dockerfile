FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY microtrax/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire microtrax package
COPY microtrax/ ./microtrax/
COPY pyproject.toml .

# Install microtrax package
RUN pip install -e .

EXPOSE 8080

CMD ["uvicorn", "microtrax.backend.app:app", "--host", "0.0.0.0", "--port", "8080"]