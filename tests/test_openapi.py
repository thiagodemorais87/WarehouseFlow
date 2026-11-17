from fastapi.testclient import TestClient

from app.main import app


def test_openapi_documents_custom_request_validation_response():
    schema = TestClient(app).get("/openapi.json").json()

    for path, method in (
        ("/auth/login", "post"),
        ("/orders/", "post"),
        ("/tasks/", "post"),
        ("/users/", "post"),
    ):
        responses = schema["paths"][path][method]["responses"]
        assert "400" in responses
        assert "422" not in responses
        assert (
            responses["400"]["content"]["application/json"]["schema"]["required"]
            == ["detail", "errors"]
        )
