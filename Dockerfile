FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY microtrax/frontend/package*.json ./

# Install frontend dependencies
RUN npm ci

# Copy frontend source and build
COPY microtrax/frontend/ ./
RUN npm run build

# Main Python image
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Copy the entire microtrax package
COPY microtrax/ ./microtrax/

# Copy built frontend from the frontend-builder stage
COPY --from=frontend-builder /app/frontend/build ./microtrax/frontend/build

EXPOSE 8080

CMD ["python", "-c", "import microtrax; microtrax.serve(port=8080, host='0.0.0.0')"]