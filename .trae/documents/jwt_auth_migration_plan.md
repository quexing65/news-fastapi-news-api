# 认证从「UUID 数据库令牌」迁移到「JWT」

## Context（为什么改）

当前 `toutiao_backend` 的认证是 **Opaque Token**：登录生成 `uuid.uuid4()` 随机串，存进数据库 `user_token` 表，前端每请求带 `Authorization: Bearer xxxx`，后端用 `get_user_by_token` **查库校验**。这是**有状态**认证，与简历中"无状态认证"的表述不符。

目标：改用 **JWT（HS256 签名）**，令牌自包含、服务端本地验签、不查 token 库，真正无状态，同时让简历表述成立。改造范围小且封闭，只影响认证一条链路，不回退其他功能。

## 现状链路（已确认）

- 生成：`create_token(db, user_id)` → `urls/users.py` 的 `uuid.uuid4()` + `UserToken` 表，[crud/users.py](file:///e:/toutiao-AI/toutiao_backend/crud/users.py#L32-L49)
- 校验：`get_user_by_token(db, token)` 查 `UserToken` + 判过期，[crud/users.py](file:///e:/toutiao-AI/toutiao_backend/crud/users.py#L63-L73)
- 注入：`get_current_user` 解析 Bearer → 调 `get_user_by_token`，[utils/auth.py](file:///e:/toutiao-AI/toutiao_backend/utils/auth.py#L10-L20)
- 调用点（grep 已确认，仅此 3 处）：
  - [routers/users.py](file:///e:/toutiao-AI/toutiao_backend/routers/users.py#L23) register
  - [routers/users.py](file:///e:/toutiao-AI/toutiao_backend/routers/users.py#L47) login
  - [utils/auth.py](file:///e:/toutiao-AI/toutiao_backend/utils/auth.py#L17) get_current_user
- `UserToken` 模型仅被 [crud/users.py](file:///e:/toutiao-AI/toutiao_backend/crud/users.py) 引用；项目无 `create_all`/建表脚本，表由外部创建。

## 改动方案

### 1. 依赖
- `pyproject.toml` dependencies 新增 `PyJWT`（`add`，版本由 uv 解析锁定 `uv.lock`）。
- 安装：`uv add pyjwt`（实现阶段执行，会更新 `pyproject.toml` + `uv.lock`）。

### 2. 新增配置文件 `config/jwt_conf.py`
沿用 `config/db_conf.py` 风格，从环境变量读取兜底默认值：
- `JWT_SECRET_KEY`：签名密钥（建议 32+ 位随机串，写入 `.env`/`.env.example`）
- `JWT_ALGORITHM = "HS256"`
- `JWT_EXPIRE_DAYS = 7`（保持现有 7 天有效期）

### 3. 新增 `utils/jwt_token.py`（签名/验签工具）
- `create_jwt_token(user_id: int) -> str`：payload 含 `{"sub": str(user_id), "exp": now+7d}`，HS256 签名。
- `decode_jwt_token(token: str) -> Optional[int]`：验签 + 判过期，成功返回 `user_id`，失败返回 `None`。

### 4. 改造 `crud/users.py`
- `create_token(db, user_id)` → 替换为 `create_jwt_token(user_id)`（不再需要 `db`，无表写入）。
- `get_user_by_token(db, token)` → 替换为 `get_user_by_id(db, user_id)`：`select(User).where(User.id == user_id)`。
- 移除 `UserToken` 的 import。
- 保留 `authenticate_user`（登录仍需校验密码，逻辑不变）。

### 5. 改造 `utils/auth.py` 的 `get_current_user`
- 从 Bearer 头解析 token → `decode_jwt_token` 得 user_id → `users.get_user_by_id(db, user_id)` 取用户。
- 解码失败返回 401（无效/过期令牌）。

### 6. 改造 `routers/users.py`
- register（L23）、login（L47）改用 `users.create_jwt_token(user.id)`。

### 7. 移除 `models/users.py` 的 `UserToken` 类
- 彻底删除该类定义（真正无状态）。数据库里的旧 `user_token` 表不删除，用户可自行手动 `DROP TABLE`；注释说明。

### 8. 配置 `.env` / `.env.example`
- 新增 `JWT_SECRET_KEY=`（生成一个随机串）。（`.env` 已在 `.gitignore`）

## 不改动
- `utils/security.py`（bcrypt 密码加密逻辑与 JWT 无关，保留）。
- `cache/`、`routers/favorite.py`、`routers/history.py`（它们只依赖 `get_current_user` 这个注入点，签名不变）。
- `models/news.py`、`schemas/`。
- 统一响应 `success_response`、异常处理器。

## 验证
1. `uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000`，Swagger 打开 `http://127.0.0.1:8000/docs`。
2. `/api/user/register` 新注册一个用户 → 拿到 `token`。
3. 用该 `token` 访问 `/api/user/info`，应返回用户信息（200 通过）。
4. 用篡改/过期 token 访问 `/api/user/info` → 返回 401，符合预期。
5. 用可选工具抓一个 JWT，在 jwt.io 验签确认 payload 含 `sub` 与 7 天 `exp`。
6. 回归：`/api/favorite/list`、`/api/history/list` 用新 token 正常返回。
7. （可选）手动 `DROP TABLE user_token`，确认登录/注册/校验均不受影响，证明已无状态。