# 🛒 淘拼商城 — 全栈电商平台

> 基于 Django REST Framework + Vue 3 的全栈电商系统，包含用户、商品、购物车、订单、支付、优惠券、评价、搜索 8 大核心模块。

## 📸 项目展示

| 首页 | 商品列表 | 商品详情 |
|:---:|:---:|:---:|
| ![首页](screenshots/01-首页.png) | ![商品列表](screenshots/02-商品列表.png) | ![商品详情](screenshots/03-商品详情.png) |

| 购物车 | 订单列表 | 优惠券中心 |
|:---:|:---:|:---:|
| ![购物车](screenshots/04-购物车.png) | ![订单列表](screenshots/05-订单列表.png) | ![优惠券中心](screenshots/06-优惠券中心.png) |

## 🏗️ 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.12 · Django 6.0 · Django REST Framework · Celery 5 |
| **前端** | Vue 3.5 · Vite 8 · Element Plus · Pinia · Vue Router 5 |
| **数据库** | MySQL 8.0 · Redis 5.0 |
| **认证** | JWT（SimpleJWT）· 双 Token 机制 |
| **测试** | pytest · requests（136 个接口自动化测试） |
| **部署** | Docker · docker-compose · Nginx |

## ✨ 核心功能

### 用户模块
- 用户注册/登录（支持用户名、手机号、邮箱三种方式）
- JWT 双 Token 认证（Access Token 2h + Refresh Token 7d + 自动刷新）
- 收货地址管理、升级商家、店铺设置

### 商品模块
- SPU/SKU 分离设计，支持多规格、独立库存
- 分类树（自关联外键）、品牌管理、图片上传
- 商品搜索（多字段模糊搜索）、热销排行、分类筛选
- Redis 缓存分类树和热销商品，写操作时主动失效

### 购物车
- **Redis Hash 存储**：key=`cart:{user_id}`，读写速度比 MySQL 快 100 倍
- 支持添加、删除、修改数量、全选/取消全选、清空
- 批量查询优化，`select_related` 避免 N+1 查询

### 订单模块
- **防超卖方案**：`transaction.atomic()` + `select_for_update()` 行锁
- 订单状态机：待付款 → 待发货 → 已发货 → 已完成 / 已取消 / 退款中
- 快照设计：OrderItem 用 IntegerField 存储 sku_id，商品改名改价不影响历史订单
- 软删除：`is_deleted` 标记，保留审计记录

### 支付模块
- 模拟支付流程（开发环境）
- 支付回调签名验证 + 状态值白名单
- 事务保证支付记录和订单状态一致性

### 优惠券
- 三种类型：满减券、折扣券、新人券
- **防超发**：`F()` 表达式原子扣减 + `unique_together` 唯一约束
- 下单时自动抵扣，支持选择优惠券

### 评价模块
- 1-5 星评分、图片评价、匿名评价
- 点赞防重复（`get_or_create` + 唯一约束 + `F()` 原子递增）
- 重复评价校验

### 搜索模块
- 搜索历史记录（Redis 缓存 + 数据库持久化）
- 搜索建议（从商品名称中提取）

## 📐 Git 提交规范

本项目遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

| 标签 | 用途 | 示例 |
|------|------|------|
| `feat` | 新增业务功能 | `feat: 新增优惠券领取接口` |
| `test` | 新增/修改测试用例 | `test: 新增营销模块(优惠券)接口测试 8个用例` |
| `docs` | 修改文档 | `docs: 更新README，添加测试方案说明` |
| `fix` | Bug 修复 | `fix: 修复优惠券超发并发问题` |
| `refactor` | 代码重构 | `refactor: 提取公共分页类到 utils` |
| `chore` | 依赖、配置修改 | `chore: 升级 Django 到 6.0.6` |

```bash
# 提交示例
git commit -m "test: 新增订单模块接口测试 22个用例"
git commit -m "docs: 添加 API 接口文档"
git commit -m "fix: 修复购物车重复添加商品报错"
```

## 🚀 快速启动

### 环境要求
- Python 3.10+ · MySQL 8.0 · Redis 5.0+ · Node.js 18+

### 后端启动

```bash
# 克隆项目
git clone https://github.com/gaopeilu/taopin.git
cd taopin

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 创建数据库
mysql -u root -p -e "CREATE DATABASE dianshang DEFAULT CHARACTER SET utf8mb4;"

# 迁移数据库
python manage.py migrate

# 创建管理员
python manage.py createsuperuser

# 启动后端
python manage.py runserver

# 启动 Celery（另开终端）
celery -A dianshang worker -l info
celery -A dianshang beat -l info
```

### 前端启动

```bash
cd frontend
npm install
npm run dev  # http://localhost:3001
```

### Docker 一键启动

```bash
docker-compose up -d
```

## 🧪 接口自动化测试

项目采用 `pytest + requests` 进行接口级自动化测试，不依赖 Django TestCase，直接发送 HTTP 请求验证 API 契约。

### 运行测试

```bash
cd test_apis
pytest -v
```

### 用例覆盖（已完成 4 个模块，共 136 个用例）

| 文件 | 用例数 | 覆盖接口 |
|------|:---:|------|
| `test_users.py` | 44 | 注册、登录、个人信息、地址管理、商家升级 |
| `test_goods.py` | 58 | 分类、品牌、SPU、SKU、图片 |
| `test_cart.py` | 26 | 添加、查询、修改数量、删除、全选、清空 |
| `test_coupons.py` | 8 | 列表、领取、我的优惠券 |
| **合计** | **136** | |

### 测试架构

```
session 级 fixture（仅登录一次）
    │
    ├── auth()        → token = test111 的 JWT
    └── seller_auth() → token = seller111 的 JWT
            │
            ▼
    各模块测试类通过 @pytest.fixture(autouse=True) 注入
```

### 优惠券防重复领取测试方案

优惠券模块的核心难点是**并发安全**：如何在多人同时抢券时不超发、不重复。后端通过两层数据库机制保证：

| 机制 | 实现 | 防护目标 |
|------|------|---------|
| `F()` 原子更新 | `UPDATE ... SET claimed_count = claimed_count + 1 WHERE claimed_count < total_count` | 防止总领取数超过发行量 |
| `unique_together` | 数据库唯一约束 `(user, coupon)` | 防止同一用户重复领取同一张券 |

接口测试从外部验证这两层防护是否生效：

| 用例 | 验证方式 | 预期响应 |
|------|---------|----------|
| **正常领取** | 登录 → 遍历列表找 `is_claimed=False` 的券 → `POST /{id}/claim/` | 200 `"领取成功"` |
| **重复领取** | 对已领取的券再次 `POST /{id}/claim/` → 触发 `IntegrityError` | 400 `"您已领取过该优惠券"` |
| **已领完** | 对 `remaining=0` 的券 `POST /{id}/claim/` → UPDATE 返回 0 行 | 400 `"优惠券已领完"` |
| **未登录** | 不带 Token 调 `/claim/` → DRF `IsAuthenticated` 拦截 | 401 |
| **不存在** | `POST /99999/claim/` → 查不到券 | 404 `"优惠券不存在"` |

> 所有异常路径的 message 均为后端源码手写，不是系统默认值，因此断言精确到 message 内容。

### 用例设计原则

- **前置条件 skip 而非 fail**：领券用例依赖"存在未领取的券"，若条件不满足则 `pytest.skip()` 跳过，不计入失败
- **接口测试只断言响应**：不查数据库验证写入，数据库正确性是后端单元测试的职责
- **session 级 token 复用**：`scope="session"` 确保全部用例只登录一次，避免 429 限流

## 📁 项目结构

```
taopin/
├── dianshang/              # Django 项目配置
│   ├── settings.py         # 全局配置（MySQL、Redis、Celery、JWT）
│   ├── celery.py           # Celery 应用配置
│   └── urls.py             # 路由入口
├── apps/                   # 业务模块
│   ├── users/              # 用户（注册、登录、地址、升级商家）
│   ├── goods/              # 商品（SPU/SKU、分类、品牌、图片）
│   ├── orders/             # 订单（创建、支付、发货、退款）
│   ├── cart/               # 购物车（Redis Hash）
│   ├── payment/            # 支付（创建、模拟支付、回调）
│   ├── marketing/          # 优惠券（领取、使用、过期）
│   ├── reviews/            # 评价（评分、点赞、图片）
│   └── search/             # 搜索（历史、建议）
├── utils/                  # 公共工具（响应格式、权限、异常处理）
├── test_apis/              # 接口自动化测试（136 个用例）
├── frontend/               # Vue 3 前端
├── screenshots/            # 项目截图
├── requirements.txt        # Python 依赖
├── docker-compose.yml      # Docker 编排
└── pytest.ini              # 测试配置
```

## 📊 API 接口总览

| 模块 | 接口数 | 主要接口 |
|------|--------|---------|
| 用户 | 13 | 注册、登录、个人信息、地址、升级商家 |
| 商品 | 5 ViewSet | 分类、品牌、SPU、SKU、图片 |
| 购物车 | 6 | 添加、删除、修改、清空、全选 |
| 订单 | 8 | 创建、支付、发货、收货、取消、退款 |
| 支付 | 4 | 创建支付、模拟支付、状态查询、回调 |
| 优惠券 | 3 | 列表、领取、我的优惠券 |
| 评价 | 4 | 列表、创建、我的评价、点赞 |
| 搜索 | 3 | 历史、清空、建议 |

## 📝 相关文档

- [Bug 修复报告](Bug报告.md)
- [代码优化清单](代码优化清单.md)
- [面试知识点总结](面试知识点总结.md)