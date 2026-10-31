FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up non-root user (UID 1000) for Hugging Face Spaces compatibility
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PORT=7860

WORKDIR $HOME/app

# Install Python requirements
COPY --chown=user:user requirements.txt .
COPY --chown=user:user backend/requirements.txt backend/
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy application source
COPY --chown=user:user . .

# Ensure storage directories exist
RUN mkdir -p backend/data uploads/pdf uploads/images uploads/generated_docs

EXPOSE 7860

CMD ["gunicorn", "--chdir", "backend", "app:app", "-w", "2", "-b", "0.0.0.0:7860", "--timeout", "180"]
