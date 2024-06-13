# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the pyproject.toml and build the package
COPY ./pyproject.toml /app/
COPY ./inference.py /app/
COPY ./training/cnn.py /app/
COPY ./training/text_dataset.py /app/

# Install build tool
RUN pip install build

# Build the package
RUN python -m build

# Install the package
RUN pip install dist/*.whl

# Run the application
ENTRYPOINT ["python", "inference.py"]
