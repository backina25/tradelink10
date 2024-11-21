
# Use Python 3.11
FROM python:3.11-slim

# Set work directory
WORKDIR /usr/src/app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Expose port
EXPOSE 8000

# Command to run the app
CMD ["python", "app/main.py"]
