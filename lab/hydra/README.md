# setup hydra

启动服务并同步数据库：

```
docker-compose -f docker-compose.yml -f docker-compose-migrate.yml up -d
```

停止所有服务：

```
docker-compose -f docker-compose.yml -f docker-compose-migrate.yml down
```

仅启动服务（不同步数据库）

```
docker-compose up -d
```


查看帮助

```
docker run -it --rm --entrypoint hydra oryd/hydra:latest help serve
docker run -it --rm --entrypoint hydra oryd/hydra:latest help clients create
```

创建 client

```
docker run --rm -it \
  -e HYDRA_ADMIN_URL=http://192.168.31.114:9001 \
  oryd/hydra:latest \
  clients create --skip-tls-verify \
    --id c1 \
    --secret some-secret \
    --grant-types authorization_code,refresh_token,client_credentials,implicit \
    --response-types token,code,id_token \
    --scope openid,offline,photos.read \
    --callbacks http://localhost:9010/callback
```

启动测试服务：

```
docker run --rm -it \
  -p 9010:9010 \
  oryd/hydra:latest \
  token user --skip-tls-verify \
    --port 9010 \
    --auth-url http://192.168.31.114:9000/oauth2/auth \
    --token-url http://192.168.31.114:9000/oauth2/token \
    --redirect http://localhost:9010/callback \
    --client-id c1 \
    --client-secret some-secret \
    --scope openid,offline,photos.read
```

http://192.168.31.114:9000/oauth2/auth?audience=&client_id=facebook-photo-backup&max_age=0&nonce=pvdlqfeavyyapngpjdefswjj&prompt=&redirect_uri=http://192.168.31.114:9010/callback&response_type=code&scope=openid+offline+photos.read&state=zskyzfhmurfdlrpjvkwtlxia
