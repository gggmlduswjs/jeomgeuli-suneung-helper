"""
Health API 테스트
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthAPI:
    """Health API 엔드포인트 테스트"""

    def test_health_check(self):
        """기본 헬스 체크 테스트"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_check_returns_database_status(self):
        """데이터베이스 상태 확인 테스트"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert "database" in data
        # database 키가 있으면 연결 상태를 나타내는 값이 있어야 함
        assert isinstance(data["database"], (str, bool, dict))

    def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "version" in data
        assert data["version"] == "2.0.0"
