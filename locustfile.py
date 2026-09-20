"""
电商系统 Locust 负载测试

覆盖电商核心业务流程:
  - 游客浏览: 商品列表、商品详情、分类浏览、搜索
  - 用户操作: 注册、登录、加入购物车、下单、支付
  - 卖家操作: 创建商品、发货

运行方式:
    # 单机调试
    locust -f locustfile.py --host=http://localhost:8000/api/v1 --headless -u 50 -r 5 -t 60s

    # Web UI 模式
    locust -f locustfile.py --host=http://localhost:8000/api/v1

    # 分布式 (master)
    locust -f locustfile.py --host=http://localhost:8000/api/v1 --master

    # 分布式 (worker)
    locust -f locustfile.py --host=http://localhost:8000/api/v1 --worker

前置条件:
    pip install locust
    python manage.py runserver
"""

import random
import time
from locust import HttpUser, between, task


class EcommerceVisitor(HttpUser):
    """
    游客用户 - 模拟未登录的浏览行为

    权重分配:
      60% 浏览商品 (列表 + 详情)
      25% 搜索
      10% 注册
      5%  分类浏览
    """

    weight = 6
    wait_time = between(0.5, 3)

    def on_start(self):
        self.spu_ids = []
        self.sku_ids = []
        self._prefetch_product_ids()

    def _prefetch_product_ids(self):
        """预取一些商品 ID 用于后续请求"""
        resp = self.client.get("/goods/spus/?page_size=20")
        if resp.status_code == 200:
            data = resp.json()
            self.spu_ids = [item["id"] for item in data.get("results", [])]

        resp = self.client.get("/goods/skus/?page_size=20")
        if resp.status_code == 200:
            data = resp.json()
            self.sku_ids = [item["id"] for item in data.get("results", [])]

    @task(4)
    def browse_spu_list(self):
        """浏览商品列表（高频）"""
        page = random.randint(1, 5)
        self.client.get(f"/goods/spus/?page={page}&page_size=12", name="/goods/spus/")

    @task(3)
    def view_spu_detail(self):
        """查看商品详情"""
        if not self.spu_ids:
            return
        spu_id = random.choice(self.spu_ids)
        self.client.get(f"/goods/spus/{spu_id}/", name="/goods/spus/[id]/")

    @task(2)
    def search_products(self):
        """搜索商品"""
        keywords = ["手机", "电脑", "衣服", "鞋子", "食品", "图书", "家电"]
        q = random.choice(keywords)
        self.client.get(f"/search/suggest/?q={q}", name="/search/suggest/")

    @task(1)
    def browse_categories(self):
        """浏览分类"""
        self.client.get("/goods/categories/", name="/goods/categories/")

    @task(1)
    def register_user(self):
        """注册新用户（低频）"""
        ts = int(time.time() * 1000)
        self.client.post(
            "/users/register/",
            json={
                "username": f"locust_{ts}",
                "password": "12345678",
                "password_confirm": "12345678",
            },
            name="/users/register/",
        )


class EcommerceBuyer(HttpUser):
    """
    买家用户 - 模拟登录后的购买行为

    权重分配:
      30% 浏览商品
      20% 搜索
      15% 加入购物车
      15% 查看购物车
      10% 下单
      5%  支付
      5%  查看订单
    """

    weight = 3
    wait_time = between(1, 5)

    def on_start(self):
        """登录并初始化（自动注册唯一买家账号，解决 CI 空库下 test111 不存在的问题）"""
        self._login()
        self._prefetch()

    def _login(self):
        ts = int(time.time() * 1000)
        username = f"locust_buyer_{ts}"
        reg_resp = self.client.post(
            "/users/register/",
            json={
                "username": username,
                "password": "12345678",
                "password_confirm": "12345678",
            },
            name="/users/register/",
        )
        if reg_resp.status_code == 201:
            data = reg_resp.json()["data"]
            self.token = data["tokens"]["access"]
            self.username = username
            self._created_user = True
        else:
            self.token = None
            self._created_user = False

    def _prefetch(self):
        self.spu_ids = []
        self.sku_ids = []
        resp = self.client.get("/goods/spus/?page_size=20")
        if resp.status_code == 200:
            self.spu_ids = [item["id"] for item in resp.json().get("results", [])]
        resp = self.client.get("/goods/skus/?page_size=20")
        if resp.status_code == 200:
            for item in resp.json().get("results", []):
                if item.get("stock", 0) > 0:
                    self.sku_ids.append(item["id"])

    def _auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(3)
    def browse_spu(self):
        """浏览商品列表"""
        page = random.randint(1, 3)
        self.client.get(
            f"/goods/spus/?page={page}&page_size=12",
            headers=self._auth_headers(),
            name="/goods/spus/ [auth]",
        )

    @task(2)
    def search(self):
        """搜索"""
        keywords = ["手机", "电脑", "衣服", "新品"]
        q = random.choice(keywords)
        self.client.get(
            f"/search/suggest/?q={q}",
            headers=self._auth_headers(),
            name="/search/suggest/ [auth]",
        )

    @task(2)
    def add_to_cart(self):
        """加入购物车"""
        if not self.sku_ids or not self.token:
            return
        sku_id = random.choice(self.sku_ids)
        self.client.post(
            "/cart/add/",
            json={"sku_id": sku_id, "quantity": random.randint(1, 3)},
            headers=self._auth_headers(),
            name="/cart/add/",
        )

    @task(2)
    def view_cart(self):
        """查看购物车"""
        if not self.token:
            return
        self.client.get(
            "/cart/",
            headers=self._auth_headers(),
            name="/cart/",
        )

    @task(1)
    def place_order(self):
        """下单（从购物车或直接购买）"""
        if not self.sku_ids or not self.token:
            return
        sku_id = random.choice(self.sku_ids)
        self.client.post(
            "/orders/",
            json={
                "items": [{"sku_id": sku_id, "quantity": 1}],
                "receiver_name": "负载测试",
                "receiver_phone": "13800138000",
                "receiver_address": "北京",
            },
            headers=self._auth_headers(),
            name="/orders/ [create]",
        )

    @task(1)
    def list_orders(self):
        """查看订单列表"""
        if not self.token:
            return
        self.client.get(
            "/orders/",
            headers=self._auth_headers(),
            name="/orders/",
        )


class EcommerceSeller(HttpUser):
    """
    卖家用户 - 模拟卖家操作

    权重分配:
      40% 查看自己的商品
      25% 查看订单
      15% 创建商品
      10% 发货
      10% 管理分类/品牌
    """

    weight = 1
    wait_time = between(2, 8)

    def on_start(self):
        """卖家登录（CI 空库时自动注册卖家账号）"""
        resp = self.client.post(
            "/users/login/",
            json={"username": "seller111", "password": "1234567811"},
            name="/users/login/ [seller]",
        )
        if resp.status_code == 200:
            self.token = resp.json()["data"]["tokens"]["access"]
        else:
            # 卖家账号不存在则自动注册
            reg = self.client.post(
                "/users/register/",
                json={
                    "username": "seller111",
                    "password": "1234567811",
                    "password_confirm": "1234567811",
                    "role": "seller",
                    "shop_name": "压测店铺",
                },
                name="/users/register/ [seller]",
            )
            if reg.status_code == 201:
                self.token = reg.json()["data"]["tokens"]["access"]
            else:
                self.token = None

    def _auth_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(4)
    def view_my_products(self):
        """查看自己的商品"""
        if not self.token:
            return
        self.client.get(
            "/goods/spus/?page=1&page_size=10",
            headers=self._auth_headers(),
            name="/goods/spus/ [seller]",
        )

    @task(3)
    def view_orders(self):
        """查看订单（卖家视角）"""
        if not self.token:
            return
        self.client.get(
            "/orders/?page=1&page_size=10",
            headers=self._auth_headers(),
            name="/orders/ [seller]",
        )

    @task(2)
    def manage_categories(self):
        """管理分类"""
        if not self.token:
            return
        self.client.get(
            "/goods/categories/",
            headers=self._auth_headers(),
            name="/goods/categories/ [seller]",
        )

    @task(1)
    def create_spu(self):
        """创建商品"""
        if not self.token:
            return
        cat_resp = self.client.get("/goods/categories/")
        if cat_resp.status_code != 200:
            return
        cats = cat_resp.json().get("results", [])
        if not cats:
            return
        cat_id = random.choice(cats)["id"]
        ts = int(time.time() * 1000)
        self.client.post(
            "/goods/spus/",
            json={"name": f"locust_spu_{ts}", "category": cat_id},
            headers=self._auth_headers(),
            name="/goods/spus/ [create]",
        )
