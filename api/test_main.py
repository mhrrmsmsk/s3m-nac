from fastapi.testclient import TestClient
from main import app  # main.py dosyasındaki 'app' objesini içe aktarıyoruz
import pytest

# Test istemcisini oluşturuyoruz
client = TestClient(app)

def test_root_endpoint():
    """Ana dizin (Root) test ediliyor"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "operational", "service": "NAC Policy Engine"}

def test_health_check():
    """Sağlık kontrolü (Health) endpoint'i test ediliyor"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_get_active_sessions():
    """Aktif oturumları listeleme endpoint'i test ediliyor"""
    response = client.get("/sessions/active")
    assert response.status_code == 200
    data = response.json()
    # Dönen JSON'da 'sessions' ve 'count' anahtarları olmalı
    assert "sessions" in data
    assert "count" in data
    assert type(data["sessions"]) == list

def test_accounting_start_payload_validation():
    """
    Accounting endpoint'ine eksik veri gönderildiğinde 
    422 Validation Error dönüp dönmediği test ediliyor (Pydantic Testi)
    """
    # Eksik payload (status_type yok)
    bad_payload = {
        "username": "TEST-USER",
        "session_id": "TEST-001",
        "nas_ip": "127.0.0.1"
    }
    response = client.post("/accounting", json=bad_payload)
    # FastAPI otomatik olarak 422 Unprocessable Entity dönmeli
    assert response.status_code == 422

def test_authorize_payload_validation():
    """Authorize endpoint'i için payload testi"""
    # Şifre eksik gönderiliyor
    bad_payload = {
        "username": "admin"
    }
    response = client.post("/author", json=bad_payload)
    assert response.status_code == 422