# Use an official Python runtime as a parent image
# Choose a version compatible with your app and Raspberry Pi (ARM architecture)
# python:3.9-slim-bullseye or python:3.11-slim-bookworm are good choices for recent Pi OS
FROM python:3.11-slim-bookworm

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir reduces image size. Some packages might need build-essentials or other system libs.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container at /app
COPY . .

# Make port 8081 available to the world outside this container
EXPOSE 8081

# Set environment variables
ENV PORT=8081
ENV HOST=0.0.0.0

# Command to run the application using waitress
CMD ["python", "-m", "mouvement.server"]