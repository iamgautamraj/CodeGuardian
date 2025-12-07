# 1. Use the official AWS Lambda Python runtime image
FROM public.ecr.aws/lambda/python:3.10

# 2. Copy requirements and install
COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

# 3. Copy your code
COPY agent.py ${LAMBDA_TASK_ROOT}
COPY main.py ${LAMBDA_TASK_ROOT}
COPY .env ${LAMBDA_TASK_ROOT} 

# 4. Set the CMD to your handler
CMD [ "main.handler" ]