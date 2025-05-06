# Base Airflow image with Python 3.10
FROM apache/airflow:2.10.4-python3.10

# Optional: Prevent pip from caching packages (saves space)
ENV PIP_NO_CACHE_DIR=true

# Copy your Python requirements into the image
COPY requirements.txt .

# Clean uninstall of conflicting preinstalled packages (safety for dbt-core)
RUN pip uninstall -y logbook || true

# Install your Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Ensure the container runs as the airflow user
USER airflow