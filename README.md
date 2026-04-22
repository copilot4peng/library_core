# my_library

单镜像部署版本的 MyBagHub。一个容器内同时运行：

- FastAPI 后端，端口 8000
- NiceGUI 前端，端口 8080

容器镜像名为 `my_library`，并支持把配置目录和存储目录映射到宿主机。

## 目录约定

- 容器内配置目录：`/config`
- 容器内配置文件：`/config/config.json`
- 容器内数据目录：`/data`

建议宿主机准备如下目录：

```bash
mkdir -p ./docker/config
mkdir -p ./docker/data
```

## 配置文件说明

在宿主机创建配置文件：`./docker/config/config.json`

示例：

```json
{
	"STORAGE_ROOT": "/data",
	"MAX_FILE_SIZE": 524288000,
	"JWT_SECRET": "change-this-secret-before-deploying-use-a-long-random-value",
	"JWT_ALGORITHM": "HS256",
	"JWT_EXPIRE_HOURS": 24,
	"BACKEND_HOST": "0.0.0.0",
	"BACKEND_PORT": 8000,
	"FRONTEND_HOST": "0.0.0.0",
	"FRONTEND_PORT": 8080,
	"BACKEND_URL": "http://localhost:8000",
	"LOG_LEVEL": "INFO"
}
```

说明：

- `STORAGE_ROOT` 在容器里应保持为 `/data`
- 宿主机真实存储路径通过 volume 映射到 `/data`
- 程序会优先读取环境变量 `MY_LIBRARY_CONFIG_PATH` 指向的配置文件，默认推荐 `/config/config.json`

## 构建镜像

在项目根目录执行：

```bash
docker build -t my_library .
```

## 直接运行

先准备宿主机配置文件：

```bash
cp config.json ./docker/config/config.json
```

```bash
docker run -d \
	--name my_library \
	-p 8000:8000 \
	-p 8080:8080 \
	-e MY_LIBRARY_CONFIG_PATH=/config/config.json \
	-v "$(pwd)/docker/config:/config" \
	-v "$(pwd)/docker/data:/data" \
	my_library
```

说明：

- `./docker/config` 会映射到容器内的 `/config`
- `./docker/data` 会映射到容器内的 `/data`
- 容器启动时会优先读取 `/config/config.json`

启动后访问：

- 前端：`http://localhost:8080`
- 后端健康检查：`http://localhost:8000/health`

## 容器内运行方式

镜像启动命令为：

```bash
python run_services.py
```

该启动器会在一个容器中同时拉起：

- `python -m backend.main`
- `python -m frontend.app`

如果其中任一进程退出，启动器会停止另一个进程并让容器退出，便于 Docker 正确感知容器状态。

## 常见操作

查看日志：

```bash
docker logs -f my_library
```

进入容器：

```bash
docker exec -it my_library /bin/sh
```

查看宿主机数据：

```bash
ls ./docker/data
```

## 兼容说明

- 仓库中原有的 `Dockerfile.backend` 和 `Dockerfile.frontend` 仍然保留
- 当前推荐使用新的单镜像 `Dockerfile`
- 当前推荐的镜像名为 `my_library`
