# 淘拼商城 - 智能电商导购平台

一个全栈电商系统，包含买家端、商家后台、购物车、订单、支付、优惠券、评价、搜索等完整业务流程。

## 技术栈

**后端**
- Python 3.12 + Django 6.0 + Django REST Framework
- MySQL 8.0 + Redis 5.0
- Celery 异步任务（订单超时取消、优惠券过期）
- JWT 认证（SimpleJWT）

**前端**
- Vue 3.5 + Vite 8
- Element Plus + Pinia + Vue Router
- Axios 请求封装（Token 自动刷新）

**基础设施**
- pytest 单元测试（51 个用例）
- Redis 缓存（购物车、验证码、商品热点）
- Celery Beat 定时任务

## 功能模块

| 模块 | 功能 |
|------|------|
| 用户 | 注册/登录（JWT双Token）、个人信息、地址管理、升级商家 |
| 商品 | SPU/SKU分离、分类树、品牌、搜索、热销排行、图片管理 |
| 购物车 | Redis存储、添加/删除/清空/全选、库存校验 |
| 订单 | 创建/支付/发货/收货/取消/退款、库存自动扣减与恢复 |
| 支付 | 模拟支付流程、支付回调、状态查询 |
| 优惠券 | 满减券/折扣券/新人券、领取/使用/过期自动标记 |
| 评价 | 1-5星评分、图片、匿名、点赞防重复 |
| 搜索 | 搜索历史、关键词建议 |

## 项目结构

```
dianshang/
├── dianshang/              # Django 项目配置
│   ├── settings.py         # 配置（MySQL、Redis、Celery、JWT）
│   ├── celery.py           # Celery 应用配置
│   └── urls.py             # 路由入口
├── apps/                   # 业务模块
│   ├── users/              # 用户模块
│   ├── goods/              # 商品模块
│   ├── orders/             # 订单模块
│   ├── cart/               # 购物车（Redis）
│   ├── payment/            # 支付模块
│   ├── marketing/          # 优惠券模块
│   ├── reviews/            # 评价模块
│   └── search/             # 搜索模块
├── utils/                  # 公共工具（响应格式、权限、异常处理）
├── tests/                  # 单元测试
├── frontend/               # Vue 3 前端
│   ├── src/
│   │   ├── api/            # API 请求封装
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 公共组件
│   │   ├── store/          # Pinia 状态管理
│   │   ├── router/         # 路由配置
│   │   └── utils/          # 前端工具函数
│   └── dist/               # 构建产物
├── requirements.txt        # Python 依赖
├── pytest.ini              # 测试配置
└── docker-compose.yml      # Docker 编排
```

## 快速启动

### 环境要求
- Python 3.10+
- MySQL 8.0
- Redis 5.0+
- Node.js 18+

### 后端启动

```bash
# 1. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux

# 2. 安装依赖
pip install -r requirements.txt

# 3. 创建数据库
mysql -u root -p -e "CREATE DATABASE dianshang DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 4. 配置环境变量（可选，有默认值）
set DJANGO_SECRET_KEY=your-secret-key
set DJANGO_DEBUG=True

# 5. 迁移数据库
python manage.py migrate

# 6. 创建管理员
python manage.py createsuperuser

# 7. 启动服务
python manage.py runserver

# 8. 启动 Celery（另开终端）
celery -A dianshang worker -l info
celery -A dianshang beat -l info
```

### 前端启动

```bash
cd frontend
npm install
npm run dev      # 开发模式 http://localhost:3001
npm run build    # 生产构建
```

### Docker 启动

```bash
docker-compose up -d
```

## 运行测试

```bash
pytest tests/ -v
```

当前测试覆盖：用户(12)、商品(10)、购物车(12)、订单(12)、支付(5) = **51 个用例**

## API 文档

所有接口统一前缀 `/api/v1/`，使用 JWT Bearer Token 认证。

| 模块 | 前缀 | 主要接口 |
|------|------|---------|
| 用户 | `/api/v1/users/` | register, login, me, password, address |
| 商品 | `/api/v1/goods/` | categories, brands, spus, skus, images |
| 购物车 | `/api/v1/cart/` | list, add, update, delete, clear, select-all |
| 订单 | `/api/v1/orders/` | create, detail, pay, cancel, ship, complete, refund |
| 支付 | `/api/v1/payment/` | create, mock-pay, status, callback |
| 优惠券 | `/api/v1/coupons/` | list, claim, mine |
| 评价 | `/api/v1/reviews/` | list, create, mine, like |
| 搜索 | `/api/v1/search/` | history, clear, suggest |
