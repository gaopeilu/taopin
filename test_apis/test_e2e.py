"""
端到端黄金链路测试 (E2E Golden Path)

一条测试覆盖电商完整业务流程:
  卖家建商品 → 注册新用户 → 登录 → 搜索 → 加购 → 下单 →
  支付 → 卖家发货 → 确认收货 → 评价

这是每次提交必跑的"烟雾报警器"——如果这条挂了，
说明核心链路断了，不需要再跑其他 215 条。
"""

import allure
import pytest
from client import APIClient, anon
from conftest import _safe_delete, unique


@allure.feature("E2E 黄金链路")
@allure.story("完整购买流程")
@allure.severity(allure.severity_level.BLOCKER)
@pytest.mark.smoke
@pytest.mark.p1
class TestGoldenPath:
    @pytest.fixture(autouse=True)
    def setup(self, seller_auth, shared_category):
        self.seller_token = seller_auth["token"]
        self.seller_client = APIClient(self.seller_token)
        self.seller_id = seller_auth["user"]["id"]
        self.cat_id = shared_category["id"]

    def test_full_purchase_flow(self):
        """
        完整电商购买流程:
        0. 卖家创建商品（SPU + SKU）
        1. 注册新用户
        2. 登录
        3. 搜索商品
        4. 加入购物车
        5. 创建订单
        6. 支付
        7. 卖家发货
        8. 确认收货
        9. 评价商品
        """
        # ============================================================
        # Step 0: 卖家创建商品（确保卖家是商品所有人，发货才不 403）
        # ============================================================
        with allure.step("0. 卖家创建商品"):
            spu_name = unique("e2e_spu")
            resp = self.seller_client.post(
                "/goods/spus/",
                json={
                    "name": spu_name,
                    "category": self.cat_id,
                    "seller": self.seller_id,
                },
            )
            assert resp.status_code == 201, f"创建 SPU 失败: {resp.text}"
            spu_id = resp.json()["id"]

            resp = self.seller_client.patch(
                f"/goods/spus/{spu_id}/",
                json={"is_on_sale": True},
            )
            assert resp.status_code == 200, f"上架失败: {resp.text}"

            resp = self.seller_client.post(
                "/goods/skus/",
                json={
                    "spu": spu_id,
                    "name": "E2E测试规格",
                    "price": "99.00",
                    "cost_price": "50.00",
                    "stock": 100,
                },
            )
            assert resp.status_code == 201, f"创建 SKU 失败: {resp.text}"
            sku_id = resp.json()["id"]

            sku_detail = anon.get(f"/goods/skus/{sku_id}")
            assert sku_detail.status_code == 200
            assert sku_detail.json()["stock"] == 100, (
                f"创建后库存应为100，实际为{sku_detail.json()['stock']}"
            )

        # ============================================================
        # Step 1: 注册新用户
        # ============================================================
        username = unique("e2e_buyer")
        with allure.step("1. 注册新用户"):
            resp = anon.post(
                "/users/register/",
                json={
                    "username": username,
                    "password": "12345678",
                    "password_confirm": "12345678",
                },
            )
            assert resp.status_code == 201, f"注册失败: {resp.text}"
            user_id = resp.json()["data"]["user"]["id"]

        with allure.step("2. 登录"):
            resp = anon.post(
                "/users/login/",
                json={"username": username, "password": "12345678"},
            )
            assert resp.status_code == 200, f"登录失败: {resp.text}"
            user_token = resp.json()["data"]["tokens"]["access"]
            buyer = APIClient(user_token)

        with allure.step("3. 搜索商品"):
            resp = anon.get(f"/goods/spus/?search={spu_name}&page_size=10")
            assert resp.status_code == 200
            results = resp.json().get("results", [])
            assert len(results) >= 1, f"搜不到商品: {spu_name}"

        with allure.step("4. 加入购物车"):
            resp = buyer.post("/cart/add/", json={"sku_id": sku_id, "quantity": 1})
            assert resp.status_code == 201, f"加购失败: {resp.text}"

            resp = buyer.get("/cart/")
            assert resp.status_code == 200
            assert len(resp.json()["data"]) >= 1

        with allure.step("5. 创建订单"):
            resp = buyer.post(
                "/orders/",
                json={
                    "items": [{"sku_id": sku_id, "quantity": 1}],
                    "receiver_name": "E2E测试用户",
                    "receiver_phone": "13800138000",
                    "receiver_address": "E2E测试地址",
                },
            )
            assert resp.status_code == 201, f"下单失败: {resp.text}"
            order_no = resp.json()["data"]["order_no"]
            assert resp.json()["data"]["status"] == "pending"

            sku_detail = anon.get(f"/goods/skus/{sku_id}")
            assert sku_detail.json()["stock"] == 99, (
                f"下单后库存应为99，实际为{sku_detail.json()['stock']}"
            )

        # ============================================================
        # Step 6: 支付
        # ============================================================
        with allure.step("6. 支付订单"):
            resp = buyer.post(f"/orders/{order_no}/pay/", json={"pay_method": "wechat"})
            assert resp.status_code == 200, f"支付失败: {resp.text}"

            order_detail = buyer.get(f"/orders/{order_no}/")
            assert order_detail.json()["status"] == "paid", (
                f"支付后状态应为paid，实际为{order_detail.json()['status']}"
            )

        with allure.step("7. 卖家发货"):
            resp = self.seller_client.post(
                f"/orders/{order_no}/ship/",
                json={"express_no": "SF1234567890"},
            )
            assert resp.status_code == 200, f"发货失败: {resp.text}"

            order_detail = buyer.get(f"/orders/{order_no}/")
            status_data = order_detail.json()
            actual_status = status_data.get("status") or status_data.get(
                "data", {}
            ).get("status")
            assert actual_status == "shipped", (
                f"发货后状态应为shipped，实际为{actual_status}"
            )

        with allure.step("8. 确认收货"):
            resp = buyer.post(f"/orders/{order_no}/complete/")
            assert resp.status_code == 200, f"收货失败: {resp.text}"

            order_detail = buyer.get(f"/orders/{order_no}/")
            status_data = order_detail.json()
            actual_status = status_data.get("status") or status_data.get(
                "data", {}
            ).get("status")
            assert actual_status == "completed", (
                f"收货后状态应为completed，实际为{actual_status}"
            )

        with allure.step("9. 评价商品"):
            resp = buyer.post(
                "/reviews/create/",
                json={
                    "sku_id": sku_id,
                    "spu_id": spu_id,
                    "order_no": order_no,
                    "rating": 5,
                    "content": "E2E测试——商品很好！",
                    "is_anonymous": False,
                },
            )
            assert resp.status_code == 201, f"评价失败: {resp.text}"

        with allure.step("清理: 删除测试用户"):
            _safe_delete(self.seller_token, f"/users/{user_id}/")

        allure.attach(
            f"订单号: {order_no}\n用户: {username}\n商品: {spu_name}\n状态: completed",
            name="E2E 测试摘要",
            attachment_type=allure.attachment_type.TEXT,
        )
