

FROM public.ecr.aws/lambda/python:3.9

# Set the working directory to /var/task (Lambda's default)
WORKDIR /var/task

# Copy app.py and other necessary files to /var/task
COPY .  /var/task/

RUN pip install --no-cache-dir -r requirements.txt

# Set the environment variable for FastAPI
ENV PYTHONUNBUFFERED=1

# Keep the handler as app.lambda_handler
CMD ["app.lambda_handler"]