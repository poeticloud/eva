FROM python:3.8-slim

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

COPY requirements/production.txt /tmp/requirements.txt

RUN set -ex \
    && sed -i "s/deb.debian.org/mirrors.aliyun.com/g" /etc/apt/sources.list \
    && sed -i "s/security.debian.org/mirrors.aliyun.com/g" /etc/apt/sources.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends vim \
    && pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r /tmp/requirements.txt \
    && apt-get clean autoclean \
    && rm -rf /var/cache/apk/* /tmp/* /var/tmp/* $HOME/.cache /var/lib/apt/lists/* /var/lib/{apt,dpkg,cache,log}/

COPY scripts /scripts
RUN chmod +x /scripts/*

COPY app /work/app
COPY aerich.ini /work/

WORKDIR /work

ENTRYPOINT ["/scripts/entrypoint.sh"]

CMD ["/scripts/start-production.sh"]
