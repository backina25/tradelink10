# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set the working directory to the root of your project
WORKDIR /usr/src/app

# Create and activate a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy the project files to the container
COPY . .

# Install dependencies in the virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 8000

# Command to run the app
CMD ["python", "app/main.py"]
