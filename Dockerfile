FROM python:3.14

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt && pip cache purge

COPY src/ .
ENV API_ROOT_PATH="/dhal"
ENV HOST=0.0.0.0

CMD ["python", "-m", "dhal_api.main"]
