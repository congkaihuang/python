FROM centos
FROM python:3.6.13-alpine
COPY second.py /
CMD ["python","first"]
