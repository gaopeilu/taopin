"""优惠券模块的接口测试"""
import requests
import pytest
from conftest import BASE_URL
from conftest import auth


class TestCoupons:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
    """优惠券模块的接口测试"""
    def test_get_coupons_list(self):
        """获取优惠券列表不登陆情况下"""
        resp = requests.get(f"{BASE_URL}/coupons/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) > 0

    def test_get_coupons(self, auth):
        """领取优惠券登录情况"""
        resp = requests.get(f"{BASE_URL}/coupons/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        # 下边的代码是找到一张没有被领取的优惠券
        cid = None
        for coupon in resp.json()["data"]:
            if not coupon["is_claimed"]:
                cid = coupon["id"]
                break
        if cid is None:
            pytest.skip("没有找到可以领取的优惠券")
        # 领取
        resp = requests.post(f"{BASE_URL}/coupons/{cid}/claim/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        assert resp.json()["message"] == "领取成功"

    def test_claim_no_auth(self):
        """未登录领取优惠券"""
        resp = requests.post(f"{BASE_URL}/coupons/1/claim/")
        assert resp.status_code == 401
        assert resp.json()["message"] == "Authentication credentials were not provided."

    def test_claim_cf_coupon(self):
        """领取优惠券重复领取"""
        resp = requests.post(f"{BASE_URL}/coupons/72/claim/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 400
        assert resp.json()["message"] == "您已领取过该优惠券"

    def test_claim_cf_coupon_no(self):
        """领取优惠券不存在"""
        resp = requests.post(f"{BASE_URL}/coupons/0/claim/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 404
        assert resp.json()["message"] == "优惠券不存在"

    def test_claim_no_number(self):
        """领取优惠券数量不足"""
        resp = requests.post(f"{BASE_URL}/coupons/77/claim/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 400
        assert resp.json()["message"] == "优惠券已领完"

    def test_claim_my_coupons(self):
        """获取我的优惠券"""
        resp = requests.get(f"{BASE_URL}/coupons/mine/", headers={
            "Authorization": f"Bearer {self.token}"
        })
        assert resp.status_code == 200
        assert len(resp.json()["results"]) > 0

    def test_claim_my_coupons_no_auth(self):
        """未登录获取我的优惠券"""
        resp = requests.get(f"{BASE_URL}/coupons/mine/")
        assert resp.status_code == 401
        assert resp.json()["message"] == "Authentication credentials were not provided."

