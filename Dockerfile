FROM python:3.8

ENV PYTHONIOENCODING=utf-8
ENV PYTHONPATH=/work
ENV PATH /usr/local/bin:$PATH

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt \
  && python3 -m compileall /work
COPY src /work

VOLUME /data
WORKDIR /work

EXPOSE 3000

CMD ["python3", "-u", "server.py"]
# test
