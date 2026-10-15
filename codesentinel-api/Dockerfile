FROM python:3.12-slim
WORKDIR /service
COPY codesentinel-api /service
COPY codesentinel-model /model
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir /model .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
