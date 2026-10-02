# 1. Use the official AWS Lambda Python runtime image
FROM public.ecr.aws/lambda/python:3.10

# 2. Copy requirements and install
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install --no-cache-dir -r requirements.txt

# 3. Copy only the application code.
#    Secrets (GITHUB_TOKEN, GROQ_API_KEY, WEBHOOK_SECRET) are NOT baked into the
#    image. Set them as environment variables on the Lambda function instead.
COPY agent.py ${LAMBDA_TASK_ROOT}
COPY main.py ${LAMBDA_TASK_ROOT}

# 4. Set the CMD to your handler
CMD [ "main.handler" ]