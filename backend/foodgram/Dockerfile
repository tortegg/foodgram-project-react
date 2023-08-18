FROM python:3.9
EXPOSE 8000
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt --no-cache-dir
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "foodgram.wsgi"]