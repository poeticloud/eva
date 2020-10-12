# eva

Open Identity Management

## 1. 项目结构说明

```shell
❯ exa -T
.
├── aerich.ini                                 #  rerich配置文件
├── app                                        #  业务代码
│  ├── __init__.py
│  ├── controllers                             #  API endpoints
│  │  ├── __init__.py
│  │  ├── hydra.py
│  │  └── identity.py
│  ├── core                                    # config或共同依赖
│  │  ├── __init__.py
│  │  └── config.py                            # 配置信息等（使用 pydantic BaseSettings管理）
│  ├── main.py                                 # **项目入口**
│  ├── migrations                              # aerich生成的迁移文件存放目录
│  │  └── models
│  │     ├── 0_20200929170837_init.json
│  │     └── old_models.py
│  ├── models.py                               # Tortorise-ORM 模型
│  ├── schemas.py                              # 供API endpoint使用的各种pydantic schema信息
│  ├── templates                               # jinja2模板存放目录
│  │  ├── consent.html
│  │  └── login.html
│  ├── tests                                   # 测试文件目录
│  │  ├── __init__.py
│  │  ├── conftest.py                          # pytest conftest
│  │  └── test_indentity.py
│  └── utils                                   # 单独，无其他依赖的工具类文件
│     ├── __init__.py
│     ├── encrypt.py
│     ├── hydra_cli.py
│     └── paginator.py
├── design
│  └── eva.graffle
├── docker-compose-migrate.yml                 # 供hydra服务初始化执行migrate使用
├── docker-compose.yaml                        # 开发用docker-compose file
├── Dockerfile                                 # 开发环境Dockerfile
├── LICENSE
├── Makefile
├── manage.py                                  # 模拟Django的manage.py，执行一些临时脚本等
├── pyproject.toml                             # black isort pytest 等配置信息
├── README.md
├── requirements                               # 项目依赖信息，使用pip-tools管理，不同场景使用不同的txt文件
│  ├── dev.in                                  # *.in 为手动维护的不带版本信息的依赖
│  ├── dev.txt                                 # *.txt 为pip-compile命令编译后生成的携带版本信息的依赖
│  ├── production.in
│  ├── production.txt
│  ├── test.in
│  └── test.txt
└── scripts                                    # 各种脚本文件存放目录
   ├── entrypoint.sh
   ├── start-develop.sh
   └── start-production.sh

```

## 2. 项目主要依赖

> Core

-   [fastapi](https://github.com/tiangolo/fastapi) API framework
-   [pydantic](https://github.com/samuelcolvin/pydantic) Data model Serialize/Deserialize/Validation, Settings Management
-   [uvicorn](https://github.com/encode/uvicorn) ASGI server
-   [typer](https://typer.tiangolo.com) CLI generator Based on Python type hints
-   [tortoise-orm](https://github.com/tortoise/tortoise-orm) async ORM
-   [aerich](https://github.com/long2ice/aerich) tortoise-orm migration manage tool

> Code Quality

-   [prospector](https://github.com/PyCQA/prospector) Linter
-   [pre-commit](https://github.com/pre-commit/pre-commit) managing git `pre-commit` hooks
-   [black](https://github.com/ambv/black) code formatter
-   [isort](https://pycqa.github.io/isort) code formatter

## 3. 本地开发环境配置

1. 克隆代码至本地

2. 创建一个新的虚拟环境（Conda / Virtualenv 等工具）版本要求 >= 3.8：

    1. `pip install -r requirements/dev.txt`
    2. 安装 pre-commit hooks `pre-commit install`

3. 使用 docker-compose 启动：

    1. 第一次执行 `docker-compose -f docker-compose.yml -f docker-compose-migrate.yml up -d`
    2. 后续开发只需要执行 `docker-compose up -d`
    3. `scripts/entrypoint.sh`脚本中会初始化好 hydra 数据库

4. 虚拟环境中直接启动

    1. `uvicorn app.main:app --reload` 或者直接执行 `make run`

5. 执行 lint

    ```shell
    make lint
    ```

6. 执行 test

    ```shell
    make test
    ```

Tips:

> 1. python manage.py createuser 创建一个用户
> 2. python manage.py dbshell 执行 pgcli，进入代码配置好的数据库环境

## 4. 数据库管理

1. 在 migrations 目录中生成迁移文件

```shell
make makemigrations
```

2. 应用、执行迁移脚本

```shell
make migrate
```

# 附

## 1. Pycharm 开发配置

参考[cookiecutter-django 的附图文档](https://github.com/pydanny/cookiecutter-django/blob/master/%7B%7Bcookiecutter.project_slug%7D%7D/docs/pycharm/configuration.rst)
