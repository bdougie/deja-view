FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY github_similarity_service.py .
COPY action.py .

# Make action.py executable
RUN chmod +x action.py

# Run the action
ENTRYPOINT ["python", "/app/action.py"]