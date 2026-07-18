FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 analytics
COPY services ./services
COPY scraper ./scraper
COPY contracts ./contracts
COPY data/samples ./data/samples
COPY alembic.ini ./
RUN mkdir -p /app/data/raw && chown -R analytics:analytics /app/data
USER analytics
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "services.analytics.fantaanalytics.wsgi:application"]
