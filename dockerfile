# Dockerfile
FROM python:3.10-slim

# Set workdir
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install pipenv

# Copy files
COPY Pipfile Pipfile.lock /app/
COPY .env /app/
COPY . /app/

# Install dependencies
RUN pipenv install --system --deploy

# Expose Streamlit default port
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", "app.py"]