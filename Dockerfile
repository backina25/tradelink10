# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /usr/src/app

# Create and activate a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Install dependencies in the virtual environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files to the container
COPY . .

# Expose the application port
EXPOSE 8000

# Command to run the app
CMD ["python", "app/main.py"]
