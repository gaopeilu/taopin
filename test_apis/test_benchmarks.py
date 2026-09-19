"""
性能基准测试

覆盖 P1 高频读接口和 P2 写链路，用 pytest-benchmark 记录耗时基线。
当接口耗时超过基线的 20%，CI 可配置为自动告警。

运行方式:
    # 只跑基准
    pytest test_apis/ -m benchmark --benchmark-only
    # 保存基线
    pytest test_apis/ -m benchmark --benchmark-only --benchmark-autosave

    # 输出 JSON 用于 CI 对比
    pytest test_apis/ -m benchmark --benchmark-only --benchmark-json=benchmarks.json

    # 对比两次基准
    pytest-benchmark compare 0001 0002
"""

import allure
import pytest
from client import APIClient, anon
from conftest import get_any_sku_id

# ====================================================================
# P1: 高频读接口 —— C 端用户直接感受到的响应速度
# ====================================================================


@allure.feature("性能基准")
@allure.story("商品读性能")
@allure.severity(allure.severity_level.NORMAL)
class TestGoodsReadBenchmark:
    """商品模块读性能基准"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    @pytest.mark.benchmark
    @pytest.mark.p1
    def test_spu_list(self, benchmark):
        """商品列表 —— 首页最高 QPS"""

        def call():
            return anon.get("/goods/spus/?page_size=20", timeout=10)

        result = benchmark(call)
        assert result.status_code == 200

    @pytest.mark.benchmark
    @pytest.mark.p1
    def test_spu_search(self, benchmark):
        """商品搜索 —— 带全文检索"""

        def call():
            return anon.get("/goods/spus/?search=手机&page_size=20", timeout=10)

        result = benchmark(call)
        assert result.status_code == 200

    @pytest.mark.benchmark
    @pytest.mark.p1
    def test_spu_detail(self, benchmark):
        """商品详情 —— 带 SKU + 图片"""

        def call():
            return self.client.get("/goods/spus/1/", timeout=10)

        result = benchmark(call)
        assert result.status_code == 200

    @pytest.mark.benchmark
    @pytest.mark.p1
    def test_categories(self, benchmark):
        """分类列表 —— 首页导航"""

        def call():
            return anon.get("/goods/categories/", timeout=10)

        result = benchmark(call)
        assert result.status_code == 200

    @pytest.mark.benchmark
    @pytest.mark.p1
    def test_skus(self, benchmark):
        """SKU 列表"""

        def call():
            return anon.get("/goods/skus/", timeout=10)

        result = benchmark(call)
        assert result.status_code == 200


@allure.feature("性能基准")
@allure.story("用户读性能")
@allure.severity(allure.severity_level.NORMAL)
class TestUserReadBenchmark:
    """用户模块读性能基准"""

    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    @pytest.mark.benchmark
    @pytest.mark.p1
    def test_user_info(self, benchmark):
        """用户信息查询"""

        def call():
            return self.client.get("/users/me/", timeout=10)

        result = benchmark(call)
        assert result.status_code == 200


# ====================================================================
# P2: 写链路 —— 影响转化率的接口
# ====================================================================


@allure.feature("性能基准")
@allure.story("订单写性能")
@allure.severity(allure.severity_level.NORMAL)
class TestOrderWriteBenchmark:
    """订单写链路性能基准"""

    @pytest.fixture(autouse=True)
    def setup(self, auth, seller_auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)
        self.seller_token = seller_auth["token"]
        self.seller_id = seller_auth["user"]["id"]

    @pytest.mark.benchmark
    @pytest.mark.p2
    def test_create_order(self, benchmark):
        """创建订单"""

        def call():
            sku_id = get_any_sku_id()
            if sku_id is None:
                pytest.skip("没有可用的 SKU")
            return self.client.post(
                "/orders/",
                json={
                    "items": [{"sku_id": sku_id, "quantity": 1}],
                    "receiver_name": "Bench",
                    "receiver_phone": "13800138000",
                    "receiver_address": "Benchmark",
                },
                timeout=10,
            )

        result = benchmark(call)
        assert result.status_code == 201

    @pytest.mark.benchmark
    @pytest.mark.p2
    def test_order_list(self, benchmark):
        """订单列表查询"""

        def call():
            return self.client.get("/orders/", timeout=10)

        result = benchmark(call)
        assert result.status_code == 200


@allure.feature("性能基准")
@allure.story("登录性能")
@allure.severity(allure.severity_level.CRITICAL)
class TestLoginBenchmark:
    """登录性能基准"""

    @pytest.mark.benchmark
    @pytest.mark.p2
    def test_login(self, benchmark):
        """登录接口 —— 用户入口"""

        def call():
            return anon.post(
                "/users/login/",
                json={"username": "test111", "password": "1234567811"},
                timeout=10,
            )

        result = benchmark(call)
        assert result.status_code == 200
