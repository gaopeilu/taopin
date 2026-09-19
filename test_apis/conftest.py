"""
测试数据工厂层 (Test Data Factory)

设计原则:
  - 通过 HTTP API 创建数据（不是直接操作数据库），保证和真实场景一致
  - 工厂 fixture 命名规则:
      * test_xxx  → 每次 function 级别新建（适合会修改数据的场景）
      * shared_xxx → module 级别共享（适合只读引用场景）
  - 工具函数: ts() 生成唯一时间戳, unique(name) 生成唯一名称
  - 自动启停: django_server fixture 自动启动 Django，pytest 结束后自动关闭
  - 数据清理: 带 yield 的 fixture 在测试后自动删除创建的数据

使用示例:
    def test_xxx(self, new_user, test_sku):
        # new_user: 临时注册的用户，含 token（用完自动删除）
        # test_sku:  自动创建的 SKU，含 id/name/price/stock（用完自动删除）
"""

import datetime
import json
import os
import subprocess
import sys
import time

import pytest
import requests
from client import APIClient, anon, url
from schemas import (
    SKUItem,
    SPUItem,
    WrappedAddressResponse,
    WrappedLoginResponse,
    WrappedOrderResponse,
    WrappedRegisterResponse,
    assert_valid,
)

# ====================================================================
# 环境配置：通过环境变量切换目标环境
# ====================================================================
# 使用: BASE_URL=http://staging.example.com/api/v1 pytest test_apis/
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000/api/v1")

# 模块级兜底值，由 persistent_sku fixture 填充
_FALLBACK_SKU_ID = None

# 清理失败收集器
_CLEANUP_FAILURES = []

# 预置账号（从环境变量读取，本地开发有默认值）
TEST_USER = os.getenv("TEST_USER", "test111")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "1234567811")
TEST_SELLER = os.getenv("TEST_SELLER", "seller111")
TEST_SELLER_PASSWORD = os.getenv("TEST_SELLER_PASSWORD", "1234567811")
TEST_ADMIN = os.getenv("TEST_ADMIN", "admin")
TEST_ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD", "admin123456")


# ====================================================================
# Allure 环境信息配置
# ====================================================================


def pytest_sessionstart(session):
    """测试会话开始时写 Allure 环境信息（此时所有插件已加载完毕）"""
    allure_dir = session.config.getoption("--alluredir", default=None)
    if allure_dir:
        os.makedirs(allure_dir, exist_ok=True)
        env_file = os.path.join(allure_dir, "environment.properties")
        with open(env_file, "w", encoding="utf-8") as f:
            f.write(f"Python={sys.version.split()[0]}\n")
            f.write(f"Platform={sys.platform}\n")
            f.write(f"Target.BaseURL={BASE_URL}\n")
            f.write(f"Target.Environment={'CI' if os.getenv('CI') else 'local'}\n")
            f.write(
                f"Report.Timestamp={datetime.datetime.now(datetime.timezone.utc).isoformat()}\n"
            )


# ====================================================================
# Allure 失败时自动附加请求/响应详情
# ====================================================================


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        try:
            import allure

            for name in (
                "req_url",
                "req_method",
                "req_body",
                "resp_status",
                "resp_body",
            ):
                val = getattr(item, f"_allure_{name}", None)
                if val is not None:
                    allure.attach(
                        json.dumps(val, ensure_ascii=False, indent=2)
                        if isinstance(val, (dict, list))
                        else str(val),
                        name=name,
                        attachment_type=allure.attachment_type.JSON
                        if isinstance(val, (dict, list))
                        else allure.attachment_type.TEXT,
                    )
        except ImportError:
            pass


# ====================================================================
# pytest-html 自定义表头：增加 模块 / 优先级 / 耗时 列
# ====================================================================


def pytest_html_results_table_header(cells):
    cells.insert(2, '<th class="sortable" data-column-type="text">模块</th>')
    cells.insert(3, '<th class="sortable" data-column-type="text">优先级</th>')
    cells.insert(4, '<th class="sortable" data-column-type="number">耗时(s)</th>')


def pytest_html_results_table_row(report, cells):
    try:
        feature = next(
            (
                m.kwargs.get("feature", "")
                for m in report.user_properties
                if m[0] == "allure_feature"
            ),
            "",
        )
        severity = next(
            (
                m.kwargs.get("severity", "")
                for m in report.user_properties
                if m[0] == "allure_severity"
            ),
            "",
        )
        duration = f"{report.duration:.2f}" if hasattr(report, "duration") else "-"
        cells.insert(2, f'<td class="col-module">{feature}</td>')
        cells.insert(3, f'<td class="col-severity">{severity}</td>')
        cells.insert(4, f'<td class="col-duration">{duration}</td>')
    except (AttributeError, IndexError, KeyError):
        cells.insert(2, '<td class="col-module">-</td>')
        cells.insert(3, '<td class="col-severity">-</td>')
        cells.insert(4, '<td class="col-duration">-</td>')


# ====================================================================
# 报告时间戳工具
# ====================================================================


def report_path(prefix="report"):
    """生成带时间戳的报告文件路径"""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    os.makedirs("reports", exist_ok=True)
    return f"reports/{prefix}_{ts}.html"


# ====================================================================
# 工具函数
# ====================================================================


def ts():
    """毫秒级时间戳，生成唯一数据"""
    return int(time.time() * 1000)


def unique(name: str) -> str:
    """生成唯一名称: test_xxx_1737225600000"""
    return f"{name}_{ts()}"


def api(path: str) -> str:
    """拼接完整 URL"""
    return f"{BASE_URL}{path}"


# ====================================================================
# Django 服务自动启停（session 级别，整个测试会话只启停一次）
# ====================================================================


@pytest.fixture(scope="session", autouse=True)
def django_server():
    """
    自动启动 Django 开发服务器，pytest 结束后自动关闭。
    不再需要手动 runserver！
    """
    proc = subprocess.Popen(
        ["python", "manage.py", "runserver", "0.0.0.0:8000", "--noreload"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # 等待服务就绪
    for _ in range(20):
        try:
            requests.get("http://localhost:8000/api/v1/", timeout=1)
            break
        except requests.ConnectionError:
            time.sleep(0.5)
    else:
        proc.terminate()
        pytest.exit("❌ Django 服务启动超时，请检查数据库迁移是否执行", returncode=1)

    yield proc

    proc.terminate()
    proc.wait(timeout=5)


# ====================================================================
# 认证 fixtures（保留原有预置账号，依赖 django_server）
# ====================================================================


@pytest.fixture(scope="session")
def auth(django_server):
    """
    普通用户登录 fixture
    整个测试 session 只登录一次，所有类共享 token

    用法:
        class TestXxx:
            @pytest.fixture(autouse=True)
            def setup(self, auth):
                self.token = auth["token"]
                self.client = APIClient(auth["token"])
                self.refresh = auth["refresh"]
    """
    resp = anon.post(
        "/users/login/",
        json={"username": TEST_USER, "password": TEST_PASSWORD},
    )
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    assert_valid(WrappedLoginResponse, resp.json(), context=f"用户登录 {TEST_USER}")
    data = resp.json()["data"]
    return {
        "token": data["tokens"]["access"],
        "refresh": data["tokens"]["refresh"],
        "user": data["user"],
    }


@pytest.fixture(scope="session")
def seller_auth(django_server):
    """
    商家登录 fixture
    用于 shop-settings / goods 写操作 / orders 发货等商家专属接口
    """
    resp = anon.post(
        "/users/login/",
        json={"username": TEST_SELLER, "password": TEST_SELLER_PASSWORD},
    )
    assert resp.status_code == 200, f"商家登录失败: {resp.text}"
    assert_valid(WrappedLoginResponse, resp.json(), context=f"商家登录 {TEST_SELLER}")
    data = resp.json()["data"]
    return {
        "token": data["tokens"]["access"],
        "refresh": data["tokens"]["refresh"],
        "user": data["user"],
    }


@pytest.fixture(scope="session")
def admin_auth(django_server):
    """
    管理员登录 fixture
    """
    resp = anon.post(
        "/users/login/",
        json={"username": TEST_ADMIN, "password": TEST_ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"管理员登录失败: {resp.text}"
    assert_valid(WrappedLoginResponse, resp.json(), context=f"管理员登录 {TEST_ADMIN}")
    data = resp.json()["data"]
    return {
        "token": data["tokens"]["access"],
        "user": data["user"],
    }


# ====================================================================
# 动态用户工厂（不依赖预置账号，每次创建新用户）
# ====================================================================


@pytest.fixture(scope="function")
def new_user(seller_auth):
    """
    创建临时普通用户（注册 + 登录）
    测试结束后自动删除用户（用 seller 账号删）

    Returns: {"token": "xxx", "client": APIClient, "user": {...}}
    """
    username = unique("testuser")
    resp = anon.post(
        "/users/register/",
        json={
            "username": username,
            "password": "12345678",
            "password_confirm": "12345678",
        },
    )
    assert resp.status_code == 201, f"注册失败: {resp.status_code} {resp.text}"
    assert_valid(WrappedRegisterResponse, resp.json(), context="注册新用户")
    data = resp.json()["data"]
    user = data["user"]
    token = data["tokens"]["access"]
    yield {
        "token": token,
        "refresh": data["tokens"]["refresh"],
        "user": user,
        "client": APIClient(token),
    }
    _safe_delete(seller_auth["token"], f"/users/{user['id']}/")


@pytest.fixture(scope="function")
def new_seller(seller_auth):
    """
    创建临时商家用户（注册 + 升级为商家）
    测试结束后自动删除

    Returns: {"token": "xxx", "client": APIClient, "user": {...}}
    """
    username = unique("testseller")
    resp = anon.post(
        "/users/register/",
        json={
            "username": username,
            "password": "12345678",
            "password_confirm": "12345678",
        },
    )
    assert resp.status_code == 201
    data = resp.json()["data"]
    user = data["user"]
    token = data["tokens"]["access"]
    client = APIClient(token)
    up = client.post("/users/upgrade/", json={"shop_name": f"临时店铺_{username}"})
    assert up.status_code == 200

    yield {"token": token, "user": user, "client": client}

    _safe_delete(seller_auth["token"], f"/users/{user['id']}/")


# ====================================================================
# 商品工厂
# ====================================================================


def _safe_delete(token, resource_path, timeout=5):
    """
    安全删除资源：忽略 404 和网络错误，避免清理失败阻塞测试。
    删除失败时记录到全局列表，session 结束统一上报告警。
    返回 True 表示确认删除成功，False 表示可能残留。
    """
    client = APIClient(token)
    try:
        resp = client.delete(resource_path, timeout=timeout)
        ok = resp.status_code in (204, 200)
        if not ok:
            _CLEANUP_FAILURES.append(
                f"[DELETE {resp.status_code}] {url(resource_path)} → {resp.text[:150]}"
            )
        return ok
    except requests.RequestException as e:
        _CLEANUP_FAILURES.append(f"[DELETE ERROR] {url(resource_path)} → {e}")
        return False


def _safe_post(token, resource_path, json_data=None, timeout=5):
    """安全 POST 请求：忽略网络错误，失败时记录"""
    client = APIClient(token)
    try:
        return client.post(resource_path, json=json_data or {}, timeout=timeout)
    except requests.RequestException as e:
        _CLEANUP_FAILURES.append(f"[POST ERROR] {url(resource_path)} → {e}")
        return None


def pytest_sessionfinish(session, exitstatus):
    """测试会话结束时，打印未清理干净的脏数据清单"""
    if _CLEANUP_FAILURES:
        print("\n" + "=" * 70)
        print(
            f"[DATA CLEANUP WARNING] {len(_CLEANUP_FAILURES)} resource(s) may not have been cleaned up"
        )
        print("=" * 70)
        for i, failure in enumerate(_CLEANUP_FAILURES, 1):
            print(f"  {i}. {failure}")
        print("=" * 70 + "\n")


@pytest.fixture(scope="session")
def shared_category(seller_auth):
    """
    Session 级共享测试分类
    创建一次，整个测试会话复用
    """
    name = unique("shared_cat")
    resp = APIClient(seller_auth["token"]).post(
        "/goods/categories/",
        json={"name": name},
    )
    assert resp.status_code == 201, f"创建分类失败: {resp.status_code} {resp.text}"
    return resp.json()


@pytest.fixture(scope="module")
def shared_brand(seller_auth):
    """
    模块级共享测试品牌
    """
    name = unique("shared_brand")
    client = APIClient(seller_auth["token"])
    resp = client.post("/goods/brands/", json={"name": name, "first_letter": "T"})
    if resp.status_code != 201:
        name = unique("shared_brand")
        resp = client.post("/goods/brands/", json={"name": name, "first_letter": "T"})
    assert resp.status_code == 201, f"创建品牌失败: {resp.status_code} {resp.text}"
    return resp.json()


@pytest.fixture(scope="function")
def test_spu(seller_auth, shared_category):
    """
    创建一个已上架的测试 SPU，测试结束后自动删除

    每次调用都新建（function 级别），避免测试间相互干扰。
    """
    client = APIClient(seller_auth["token"])
    name = unique("test_spu")
    resp = client.post(
        "/goods/spus/",
        json={"name": name, "category": shared_category["id"]},
    )
    assert resp.status_code == 201, f"创建SPU失败: {resp.status_code} {resp.text}"
    assert_valid(SPUItem, resp.json(), context="创建 SPU")
    spu = resp.json()
    spu_id = spu["id"]

    client.patch(f"/goods/spus/{spu_id}/", json={"is_on_sale": True})

    yield spu

    _safe_delete(seller_auth["token"], f"/goods/spus/{spu_id}/")


@pytest.fixture(scope="function")
def test_sku(seller_auth, test_spu):
    """
    创建一个测试 SKU（自动关联 test_spu），测试结束后自动删除

    Returns: {"id": int, "name": str, "price": str, "stock": int, ...}
    """
    name = unique("test_sku")
    resp = APIClient(seller_auth["token"]).post(
        "/goods/skus/",
        json={"spu": test_spu["id"], "name": name, "price": "88.00", "stock": 100},
    )
    assert resp.status_code == 201, f"创建SKU失败: {resp.status_code} {resp.text}"
    assert_valid(SKUItem, resp.json(), context="创建 SKU")
    sku = resp.json()
    sku["price"] = "88.00"
    sku["stock"] = 100

    yield sku

    _safe_delete(seller_auth["token"], f"/goods/skus/{sku['id']}/")


@pytest.fixture(scope="session", autouse=True)
def persistent_sku(seller_auth, shared_category):
    """
    【Session 级别】持久测试 SKU，整个测试运行期间只创建一次

    用于 get_any_sku_id() 的最后兜底，
    确保即使数据库里全是孤儿 SKU，也至少有一个可用的
    """
    client = APIClient(seller_auth["token"])
    name = f"持久测试SKU-{ts()}"
    spu_resp = client.post(
        "/goods/spus/",
        json={"name": f"持久测试SPU-{ts()}", "category": shared_category["id"]},
    )
    assert spu_resp.status_code == 201, f"持久SPU创建失败: {spu_resp.text}"
    spu_data = spu_resp.json()
    spu_id = spu_data["id"]
    patch_resp = client.patch(
        f"/goods/spus/{spu_id}/",
        json={"is_on_sale": True, "description": "持久 SPU，供全量测试使用"},
    )
    assert patch_resp.status_code == 200, f"持久SPU上架失败: {patch_resp.text}"

    sku_resp = client.post(
        "/goods/skus/",
        json={"spu": spu_id, "name": name, "price": "99.00", "stock": 9999},
    )
    assert sku_resp.status_code == 201, f"持久SKU创建失败: {sku_resp.text}"
    sku = sku_resp.json()
    sku["price"] = "99.00"
    sku["stock"] = 9999

    global _FALLBACK_SKU_ID
    _FALLBACK_SKU_ID = sku["id"]

    yield sku

    _FALLBACK_SKU_ID = None
    _safe_delete(seller_auth["token"], f"/goods/skus/{sku['id']}/")
    _safe_delete(seller_auth["token"], f"/goods/spus/{spu_id}/")


def get_any_sku_id():
    """
    获取任意一个可用的 SKU ID（不创建新数据，从已有列表取）

    优先返回 persistent_sku（session 级别，每次测试会话新鲜创建，最可靠），
    找不到时才从 SKU 列表遍历筛选，作为兜底。
    """
    if _FALLBACK_SKU_ID is not None:
        return _FALLBACK_SKU_ID

    resp = anon.get("/goods/skus/")
    if resp.status_code == 200:
        results = resp.json().get("results", [])
        for sku in results:
            if sku.get("stock", 0) <= 0:
                continue
            spu_id = sku.get("spu")
            if spu_id:
                spu_resp = anon.get(f"/goods/spus/{spu_id}/")
                if spu_resp.status_code == 200 and spu_resp.json().get("is_on_sale"):
                    return sku["id"]
    return None


# ====================================================================
# 地址工厂
# ====================================================================


@pytest.fixture(scope="function")
def test_address(auth):
    """
    创建一个测试收货地址，测试结束后自动删除

    Returns: {"id": int, "receiver_name": str, "receiver_phone": str, ...}
    """
    resp = APIClient(auth["token"]).post(
        "/users/address/",
        json={
            "receiver_name": "工厂测试",
            "receiver_phone": "13800138000",
            "province": "广东省",
            "city": "深圳市",
            "district": "南山区",
            "detail_address": f"工厂路{ts()}号",
        },
    )
    assert resp.status_code == 201, f"创建地址失败: {resp.status_code} {resp.text}"
    assert_valid(WrappedAddressResponse, resp.json(), context="创建地址")
    addr = resp.json()["data"]

    yield addr

    _safe_delete(auth["token"], f"/users/address/{addr['id']}/")


# ====================================================================
# 订单工厂
# ====================================================================


def create_order(token, sku_id, **kwargs):
    """
    底层创建订单函数（可被测试直接调用）

    Args:
        token: 用户 token
        sku_id: SKU ID
        **kwargs: quantity, receiver_name, receiver_phone, receiver_address, remark, coupon_id

    Returns: requests.Response 对象
    """
    data = {
        "items": [{"sku_id": sku_id, "quantity": kwargs.pop("quantity", 1)}],
        "receiver_name": kwargs.pop("receiver_name", "工厂测试"),
        "receiver_phone": kwargs.pop("receiver_phone", "13800138000"),
        "receiver_address": kwargs.pop("receiver_address", "工厂测试地址"),
    }
    data.update(kwargs)
    return APIClient(token).post("/orders/", json=data)


@pytest.fixture(scope="function")
def test_order(auth):
    """
    创建一个待付款订单，测试结束后自动取消+删除

    Returns: {"order_no": str, "status": "pending", "items": [...], ...}
    """
    sku_id = get_any_sku_id()
    if sku_id is None:
        pytest.skip("没有可用 SKU，无法创建订单")
    resp = create_order(auth["token"], sku_id)
    assert resp.status_code == 201, f"创建订单失败: {resp.status_code} {resp.text}"
    assert_valid(WrappedOrderResponse, resp.json(), context="创建订单")
    order = resp.json()["data"]

    yield order

    # 清理：先取消再删除
    _safe_post(auth["token"], f"/orders/{order['order_no']}/cancel/")
    _safe_delete(auth["token"], f"/orders/{order['order_no']}/")


@pytest.fixture(scope="function")
def paid_order(auth):
    """
    创建一个已支付订单（pending → pay → paid），测试结束后尝试取消+删除

    Returns: order 对象（status="paid"）
    """
    sku_id = get_any_sku_id()
    if sku_id is None:
        pytest.skip("没有可用 SKU，无法创建订单")
    resp = create_order(auth["token"], sku_id)
    assert resp.status_code == 201
    order = resp.json()["data"]
    order_no = order["order_no"]

    pay_resp = APIClient(auth["token"]).post(
        f"/orders/{order_no}/pay/",
        json={"pay_method": "wechat"},
    )
    assert pay_resp.status_code == 200, (
        f"支付失败: {pay_resp.status_code} {pay_resp.text}"
    )

    yield order

    # 清理：已支付的先取消（如果允许）再删除
    _safe_post(auth["token"], f"/orders/{order_no}/cancel/")
    _safe_delete(auth["token"], f"/orders/{order_no}/")


@pytest.fixture(scope="function")
def shipped_order(auth, seller_auth, test_sku, new_user):
    """
    创建一个已发货订单（完整链路：创建 SPU/SKU → 下单 → 支付 → 发货）
    测试结束后尝试确认收货 → 删除

    Returns: {"order_no": str, "status": "shipped", ...}
    """
    user_token = new_user["token"]
    user_client = new_user["client"]
    seller_client = APIClient(seller_auth["token"])

    # seller 创建可售 SKU（复用 test_sku 的 SPU 就不用额外创建）
    # shipped_order 需要自己管理 SPU/SKU 生命周期，这里直接用 test_sku
    sku_id = test_sku["id"]

    # user 下单
    resp = create_order(user_token, sku_id)
    assert resp.status_code == 201
    order_no = resp.json()["data"]["order_no"]

    # user 支付
    pay_resp = user_client.post(
        f"/orders/{order_no}/pay/", json={"pay_method": "wechat"}
    )
    assert pay_resp.status_code == 200

    # seller 发货
    ship_resp = seller_client.post(
        f"/orders/{order_no}/ship/", json={"express_no": "SF1234567890"}
    )
    assert ship_resp.status_code == 200, (
        f"发货失败: {ship_resp.status_code} {ship_resp.text}"
    )

    # 返回最新订单状态
    get_resp = user_client.get(f"/orders/{order_no}/")

    yield get_resp.json()

    # 清理：确认收货 → 删除
    _safe_post(user_token, f"/orders/{order_no}/complete/")
    _safe_delete(user_token, f"/orders/{order_no}/")


def _get_or_create_category_id(token):
    """获取或创建一个分类 ID"""
    resp = anon.get("/goods/categories/")
    results = resp.json().get("results", [])
    if results:
        return results[0]["id"]
    name = unique("auto_cat")
    resp = APIClient(token).post(
        "/goods/categories/",
        json={"name": name},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ====================================================================
# 购物车清理（辅助）
# ====================================================================


@pytest.fixture(scope="function")
def clean_cart(auth):
    """
    确保测试前后购物车为空
    用法: 在需要隔离 cart 数据的类里 autouse
    """
    APIClient(auth["token"]).delete("/cart/clear/")
    yield
    APIClient(auth["token"]).delete("/cart/clear/")
