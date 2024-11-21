# Use Python 3.11 as the base image
FROM python:3.11-slim

# Set the working directory to the root of your project
WORKDIR /usr/src/app

# Create and activate a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements file first to leverage build cache
COPY requirements.txt .

# Install dependencies (cached unless requirements.txt changes)
#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

# Copy only the necessary files and folders
COPY app/ ./app
COPY config.py .

# Expose the application port
# The default value of PORT is 10000 for all Render web services 
EXPOSE 10000

# Command to run the app
CMD ["python", "app/main.py"]
#CMD ["sleep", "infinity"]
