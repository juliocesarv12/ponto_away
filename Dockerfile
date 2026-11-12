FROM mcr.microsoft.com/playwright/python:v1.65.1-noble

USER root
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src

ENV PYTHONUNBUFFERED=1 \
    TZ=America/Porto_Velho \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

CMD ["python", "-m", "src.main"]
