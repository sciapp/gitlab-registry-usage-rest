FROM python:3.6-alpine as builder
LABEL maintainer="Ingo Heimbach <i.heimbach@fz-juelich.de>"

RUN apk --no-cache add build-base git libffi-dev openssl-dev && \
    pip install --no-cache-dir "git+${CI_REPOSITORY_URL}@${CI_COMMIT_REF_NAME}"


FROM python:3.6-alpine

RUN apk --no-cache add libffi openssl

COPY --from=builder /usr/local/lib/python3.6/site-packages /usr/local/lib/python3.6/

EXPOSE 80

ENTRYPOINT ["python3", "-m", "gitlab_registry_usage_rest"]
