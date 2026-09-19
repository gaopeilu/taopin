"""搜索模块的接口测试"""

import allure
import pytest
from client import APIClient, anon


# ==================== 搜索历史列表 ====================
@allure.feature("搜索模块")
@allure.story("搜索历史")
@allure.severity(allure.severity_level.NORMAL)
class TestSearchHistory:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_history_success(self):
        """已登录查看搜索历史"""
        resp = self.client.get("/search/history/")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert "data" in resp.json()

    def test_history_no_auth(self):
        """未登录"""
        resp = anon.get("/search/history/")
        assert resp.status_code == 401


# ==================== 清空搜索历史 ====================
@allure.feature("搜索模块")
@allure.story("清空历史")
@allure.severity(allure.severity_level.NORMAL)
class TestSearchHistoryClear:
    @pytest.fixture(autouse=True)
    def setup(self, auth):
        self.token = auth["token"]
        self.client = APIClient(self.token)

    def test_clear_success(self):
        """正常清空"""
        resp = self.client.delete("/search/history/clear/")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert resp.json()["message"] == "已清空"

        # 清空后再查应该为空
        resp = self.client.get("/search/history/")
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 0

    def test_clear_no_auth(self):
        """未登录"""
        resp = anon.delete("/search/history/clear/")
        assert resp.status_code == 401


# ==================== 搜索建议 ====================
@allure.feature("搜索模块")
@allure.story("搜索建议")
@allure.severity(allure.severity_level.NORMAL)
class TestSearchSuggest:
    def test_suggest_with_query(self):
        """带关键词搜索"""
        resp = anon.get("/search/suggest/?q=三只松鼠")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert len(resp.json()["data"]) > 0
        for item in resp.json()["data"]:
            assert isinstance(item, str)

    def test_suggest_empty_query(self):
        """空关键词"""
        resp = anon.get("/search/suggest/?q=")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert resp.json()["data"] == []

    def test_suggest_no_query_param(self):
        """无 q 参数"""
        resp = anon.get("/search/suggest/")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert resp.json()["data"] == []

    def test_suggest_no_results(self):
        """无匹配结果"""
        resp = anon.get("/search/suggest/?q=zzznotexist999")
        assert resp.status_code == 200
        assert resp.json()["code"] == 200
        assert resp.json()["data"] == []

    def test_suggest_records_history(self, auth):
        """已登录用户的搜索会记录到历史"""
        client = APIClient(auth["token"])
        client.get("/search/suggest/?q=手机")
        resp = client.get("/search/history/")
        assert resp.status_code == 200
        keywords = [h["keyword"] for h in resp.json()["data"]]
        assert "手机" in keywords
