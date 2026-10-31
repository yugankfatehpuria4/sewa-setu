FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir Flask==2.2.5 Werkzeug==2.3.8
COPY app.py .
EXPOSE 8025
CMD ["python", "app.py"]
