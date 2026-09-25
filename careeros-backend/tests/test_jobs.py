"""Job posting endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_job(client: AsyncClient) -> None:
    payload = {
        "title": "Senior Backend Engineer",
        "description": "FastAPI + SQLAlchemy role",
        "location": "Remote",
        "remote_type": "remote",
        "salary_min": 120000,
        "salary_max": 160000,
    }
    response = await client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == payload["title"]
    assert body["id"] > 0


@pytest.mark.asyncio
async def test_list_jobs_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/jobs")
    assert response.status_code == 200
    body = response.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_get_job_not_found(client: AsyncClient) -> None:
    response = await client.get("/api/v1/jobs/9999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_job(client: AsyncClient) -> None:
    payload = {"title": "Temp Role"}
    create_resp = await client.post("/api/v1/jobs", json=payload)
    job_id = create_resp.json()["id"]

    delete_resp = await client.delete(f"/api/v1/jobs/{job_id}")
    assert delete_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/jobs/{job_id}")
    assert get_resp.status_code == 404
