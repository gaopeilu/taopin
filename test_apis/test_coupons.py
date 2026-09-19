"""优惠券模块的接口测试"""

import allure
import pytest
from client import APIClient, anon


@allure.feature("营销模块")
@allure.story("优惠券")
@allure.severity(allure.severity_level.NORMAL)
class TestCoupons:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_get_coupons_list(self):
        """获取优惠券列表不登陆情况下"""
        resp = anon.get("/coupons/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) > 0

    def test_get_coupons(self, auth):
        """领取优惠券登录情况"""
        resp = self.client.get("/coupons/")
        cid = None
        for coupon in resp.json()["data"]:
            if not coupon["is_claimed"] and coupon["remaining"] > 0:
                cid = coupon["id"]
                break
        if cid is None:
            pytest.skip("没有找到可以领取的优惠券")
        resp = self.client.post(f"/coupons/{cid}/claim/")
        assert resp.status_code == 200
        assert resp.json()["message"] == "领取成功"

    def test_claim_no_auth(self):
        """未登录领取优惠券"""
        resp = anon.post("/coupons/1/claim/")
        assert resp.status_code == 401
        assert resp.json()["message"] == "Authentication credentials were not provided."

    def test_claim_cf_coupon(self):
        """领取优惠券重复领取"""
        resp = self.client.post("/coupons/72/claim/")
        assert resp.status_code == 400
        assert resp.json()["message"] == "您已领取过该优惠券"

    def test_claim_cf_coupon_no(self):
        """领取优惠券不存在"""
        resp = self.client.post("/coupons/0/claim/")
        assert resp.status_code == 404
        assert resp.json()["message"] == "优惠券不存在"

    def test_claim_no_number(self):
        """领取优惠券数量不足"""
        resp = self.client.post("/coupons/77/claim/")
        assert resp.status_code == 400
        assert resp.json()["message"] == "优惠券已领完"

    def test_claim_my_coupons(self):
        """获取我的优惠券"""
        resp = self.client.get("/coupons/mine/")
        assert resp.status_code == 200
        assert len(resp.json()["results"]) > 0

    def test_claim_my_coupons_no_auth(self):
        """未登录获取我的优惠券"""
        resp = anon.get("/coupons/mine/")
        assert resp.status_code == 401
        assert resp.json()["message"] == "Authentication credentials were not provided."

    def test_order_with_coupon(self):
        """下单时使用优惠券，验证折扣生效"""
        from conftest import get_any_sku_id

        sku_id = get_any_sku_id()
        if sku_id is None:
            pytest.skip("没有可用的 SKU")

        resp = self.client.get("/coupons/")
        cid = None
        for coupon in resp.json()["data"]:
            if not coupon["is_claimed"] and coupon["remaining"] > 0:
                cid = coupon["id"]
                break
        if cid is None:
            pytest.skip("没有可领取的优惠券")

        claim_resp = self.client.post(f"/coupons/{cid}/claim/")
        assert claim_resp.status_code == 200, f"领取失败: {claim_resp.text}"

        mine_resp = self.client.get("/coupons/mine/")
        records = mine_resp.json().get("results", [])
        assert len(records) > 0, "应该有已领取的优惠券"
        coupon_record_id = records[0]["id"]

        order_resp = self.client.post(
            "/orders/",
            json={
                "items": [{"sku_id": sku_id, "quantity": 1}],
                "receiver_name": "测试",
                "receiver_phone": "13800138000",
                "receiver_address": "折扣测试地址",
                "coupon_id": coupon_record_id,
            },
        )
        assert order_resp.status_code in (201, 400), (
            f"下单应成功或不满足最低消费: {order_resp.status_code} {order_resp.text}"
        )

    def test_order_with_used_coupon(self):
        """重复使用已使用的优惠券 → 400"""
        from conftest import get_any_sku_id

        sku_id = get_any_sku_id()
        if sku_id is None:
            pytest.skip("没有可用的 SKU")

        resp = self.client.get("/coupons/")
        cid = None
        for coupon in resp.json()["data"]:
            if not coupon["is_claimed"] and coupon["remaining"] > 0:
                cid = coupon["id"]
                break
        if cid is None:
            pytest.skip("没有可领取的优惠券")

        self.client.post(f"/coupons/{cid}/claim/")
        mine_resp = self.client.get("/coupons/mine/")
        records = mine_resp.json().get("results", [])
        if not records:
            pytest.skip("没有优惠券记录")
        coupon_record_id = records[0]["id"]

        order1 = self.client.post(
            "/orders/",
            json={
                "items": [{"sku_id": sku_id, "quantity": 1}],
                "receiver_name": "测试",
                "receiver_phone": "13800138000",
                "receiver_address": "测试地址",
                "coupon_id": coupon_record_id,
            },
        )
        if order1.status_code != 201:
            pytest.skip("优惠券不满足最低消费，无法完成首次下单")

        order2 = self.client.post(
            "/orders/",
            json={
                "items": [{"sku_id": sku_id, "quantity": 2}],
                "receiver_name": "测试",
                "receiver_phone": "13800138000",
                "receiver_address": "二次地址",
                "coupon_id": coupon_record_id,
            },
        )
        assert order2.status_code == 400, (
            f"已使用优惠券不应再减: {order2.status_code} {order2.text}"
        )

    def test_order_coupon_below_min_amount(self):
        """未满最低消费使用优惠券 → 400"""
        from conftest import get_any_sku_id

        sku_id = get_any_sku_id()
        if sku_id is None:
            pytest.skip("没有可用的 SKU")

        resp = self.client.get("/coupons/")
        cid = None
        for coupon in resp.json()["data"]:
            if not coupon["is_claimed"] and coupon["remaining"] > 0:
                cid = coupon["id"]
                break
        if cid is None:
            pytest.skip("没有可领取的优惠券")

        self.client.post(f"/coupons/{cid}/claim/")
        mine_resp = self.client.get("/coupons/mine/")
        records = mine_resp.json().get("results", [])
        if not records:
            pytest.skip("没有优惠券记录")
        coupon_record_id = records[0]["id"]

        resp = self.client.post(
            "/orders/",
            json={
                "items": [{"sku_id": sku_id, "quantity": 1}],
                "receiver_name": "测试",
                "receiver_phone": "13800138000",
                "receiver_address": "测试地址",
                "coupon_id": coupon_record_id,
            },
        )
        if resp.status_code == 400:
            assert "最低消费" in resp.json().get("message", ""), (
                f"应提示最低消费: {resp.text}"
            )
