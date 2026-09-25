"""Integration tests for the Document module: CV/CL generation, versioning, LaTeX compilation.

Tests the document service layer with mocked LaTeX subprocess execution
to avoid requiring texlive in the test environment.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentType
from app.schemas.document import DocumentGenerateRequest
from app.services import document_service


# =============================================================================
# DOCUMENT GENERATION TESTS
# =============================================================================


class TestGenerateDocument:
    """``generate_document`` creates Document rows and computes versions."""

    @pytest.mark.asyncio
    async def test_generate_creates_pending_document(
        self, db_session: AsyncSession, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """Generating a document creates a row with status 'pending'."""
        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir):
            payload = DocumentGenerateRequest(
                job_posting_id=sample_job.id,
                document_type="cv",
                template_name="moderncv",
            )
            result = await document_service.generate_document(db_session, payload)

        assert result.id > 0
        assert result.status == "pending"

        # Verify DB state
        doc = await db_session.get(Document, result.id)
        assert doc is not None
        assert doc.status == "pending"
        assert doc.document_type == "cv"
        assert doc.version == 1

    @pytest.mark.asyncio
    async def test_generate_increments_version(
        self, db_session: AsyncSession, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """Subsequent generations increment the version number."""
        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir):
            payload = DocumentGenerateRequest(
                job_posting_id=sample_job.id,
                document_type="cv",
                template_name="moderncv",
            )
            v1 = await document_service.generate_document(db_session, payload)
            v2 = await document_service.generate_document(db_session, payload)

        # Verify versions by querying the DB
        from app.models.document import Document
        from sqlalchemy import select

        result = await db_session.execute(
            select(Document.version).where(Document.id.in_([v1.id, v2.id]))
        )
        versions = sorted(result.scalars().all())
        assert versions == [1, 2]

    @pytest.mark.asyncio
    async def test_generate_cover_letter_type(
        self, db_session: AsyncSession, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """Generation works for cover_letter documents too."""
        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir):
            payload = DocumentGenerateRequest(
                job_posting_id=sample_job.id,
                document_type="cover_letter",
                template_name="mycoverletter",
            )
            result = await document_service.generate_document(db_session, payload)

        assert result.status == "pending"
        doc = await db_session.get(Document, result.id)
        assert doc is not None
        assert doc.document_type == "cover_letter"

    @pytest.mark.asyncio
    async def test_generate_invalid_type_raises(self, db_session: AsyncSession) -> None:
        """Invalid document_type raises an error (Pydantic ValidationError)."""
        # Pydantic validates the literal type before the service is called,
        # so the error is a ValidationError from pydantic, not the service.
        with pytest.raises(Exception):  # pydantic.ValidationError
            DocumentGenerateRequest(
                job_posting_id=1,
                document_type="resume",  # invalid
                template_name="moderncv",
            )

    @pytest.mark.asyncio
    async def test_generate_stores_variables(
        self, db_session: AsyncSession, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """Template variables are stored as JSON."""
        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir):
            payload = DocumentGenerateRequest(
                job_posting_id=sample_job.id,
                document_type="cv",
                template_name="moderncv",
                variables={"name": "John Doe", "company": "Acme"},
            )
            result = await document_service.generate_document(db_session, payload)

        doc = await db_session.get(Document, result.id)
        assert doc is not None
        assert doc.variables_json is not None
        variables = json.loads(doc.variables_json)
        assert variables["name"] == "John Doe"
        assert variables["company"] == "Acme"


# =============================================================================
# LATEX COMPILATION TESTS (mocked subprocess)
# =============================================================================


class TestCompileLatex:
    """``compile_latex`` runs the LaTeX engine and updates the document."""

    @pytest.mark.asyncio
    async def test_compile_success(
        self,
        db_session: AsyncSession,
        sample_job: JobPosting,
        tmp_storage_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Successful compilation marks the document as 'ready'."""
        # Create a fake template file
        templates_root = tmp_storage_dir / "templates"
        cv_dir = templates_root / "cv"
        cv_dir.mkdir(parents=True, exist_ok=True)
        tex_file = cv_dir / "moderncv.tex"
        tex_file.write_text("\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}")

        # Mock subprocess: use a real async coroutine for create_subprocess_exec
        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"Output written", b""))
        mock_proc.returncode = 0
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()

        async def _mock_create_subprocess(*args, **kwargs):
            return mock_proc

        async def _mock_wait_for(coro, timeout=None):
            return await coro

        monkeypatch.setattr(
            document_service.asyncio, "create_subprocess_exec", _mock_create_subprocess
        )
        monkeypatch.setattr(
            document_service.asyncio, "wait_for", _mock_wait_for
        )

        # Create a fake PDF output so the compile step finds it
        def _mock_build_output_dir(job_posting_id, doc_type, version):
            out = tmp_storage_dir / f"job_{job_posting_id}" / f"{doc_type}_v{version}"
            out.mkdir(parents=True, exist_ok=True)
            # Pre-create the PDF that the compile step expects to find
            pdf_path = out / "moderncv.pdf"
            pdf_path.write_bytes(b"%PDF-1.4 fake content")
            return out

        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir), \
             patch.object(document_service, "_templates_root", return_value=templates_root), \
             patch.object(document_service, "_build_output_dir", _mock_build_output_dir):
            payload = DocumentGenerateRequest(
                job_posting_id=sample_job.id,
                document_type="cv",
                template_name="moderncv",
            )
            doc_result = await document_service.generate_document(db_session, payload)
            result = await document_service.compile_latex(doc_result.id, db_session)

        assert result.success is True
        assert result.pdf_path is not None

        doc = await db_session.get(Document, doc_result.id)
        assert doc is not None
        assert doc.status == "ready"
        assert doc.pdf_path is not None
        assert doc.file_size_bytes is not None

    @pytest.mark.asyncio
    async def test_compile_failure(
        self,
        db_session: AsyncSession,
        sample_job: JobPosting,
        tmp_storage_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Failed compilation marks the document as 'failed'."""
        templates_root = tmp_storage_dir / "templates"
        cv_dir = templates_root / "cv"
        cv_dir.mkdir(parents=True, exist_ok=True)
        tex_file = cv_dir / "moderncv.tex"
        tex_file.write_text("\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}")

        mock_proc = AsyncMock()
        mock_proc.communicate = AsyncMock(return_value=(b"", b"! Undefined control sequence."))
        mock_proc.returncode = 1
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()

        async def _mock_create_subprocess(*args, **kwargs):
            return mock_proc

        async def _mock_wait_for(coro, timeout=None):
            return await coro

        monkeypatch.setattr(
            document_service.asyncio, "create_subprocess_exec", _mock_create_subprocess
        )
        monkeypatch.setattr(
            document_service.asyncio, "wait_for", _mock_wait_for
        )

        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir), \
             patch.object(document_service, "_templates_root", return_value=templates_root):
            payload = DocumentGenerateRequest(
                job_posting_id=sample_job.id,
                document_type="cv",
                template_name="moderncv",
            )
            doc_result = await document_service.generate_document(db_session, payload)
            result = await document_service.compile_latex(doc_result.id, db_session)

        assert result.success is False
        doc = await db_session.get(Document, doc_result.id)
        assert doc is not None
        assert doc.status == "failed"
        assert doc.compilation_log is not None

    @pytest.mark.asyncio
    async def test_compile_timeout(
        self,
        db_session: AsyncSession,
        sample_job: JobPosting,
        tmp_storage_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Timeout during compilation marks the document as 'failed'."""
        import asyncio

        templates_root = tmp_storage_dir / "templates"
        cv_dir = templates_root / "cv"
        cv_dir.mkdir(parents=True, exist_ok=True)
        tex_file = cv_dir / "moderncv.tex"
        tex_file.write_text("\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}")

        mock_proc = AsyncMock()
        mock_proc.kill = MagicMock()
        mock_proc.wait = AsyncMock()

        async def _mock_create_subprocess(*args, **kwargs):
            return mock_proc

        async def _timeout(*args, **kwargs):
            raise asyncio.TimeoutError()

        monkeypatch.setattr(
            document_service.asyncio, "create_subprocess_exec", _mock_create_subprocess
        )
        monkeypatch.setattr(document_service.asyncio, "wait_for", _timeout)
        monkeypatch.setattr(document_service, "COMPILE_TIMEOUT", 1)

        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir), \
             patch.object(document_service, "_templates_root", return_value=templates_root):
            payload = DocumentGenerateRequest(
                job_posting_id=sample_job.id,
                document_type="cv",
                template_name="moderncv",
            )
            doc_result = await document_service.generate_document(db_session, payload)
            result = await document_service.compile_latex(doc_result.id, db_session)

        assert result.success is False
        doc = await db_session.get(Document, doc_result.id)
        assert doc is not None
        assert doc.status == "failed"

    @pytest.mark.asyncio
    async def test_compile_missing_template(
        self,
        db_session: AsyncSession,
        sample_job: JobPosting,
        tmp_storage_dir: Path,
    ) -> None:
        """Missing template file marks the document as 'failed'."""
        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir), \
             patch.object(document_service, "_templates_root", return_value=tmp_storage_dir / "templates"):
            payload = DocumentGenerateRequest(
                job_posting_id=sample_job.id,
                document_type="cv",
                template_name="nonexistent_template",
            )
            doc_result = await document_service.generate_document(db_session, payload)
            result = await document_service.compile_latex(doc_result.id, db_session)

        assert result.success is False
        doc = await db_session.get(Document, doc_result.id)
        assert doc is not None
        assert doc.status == "failed"
        assert "not found" in (doc.compilation_log or "").lower()

    @pytest.mark.asyncio
    async def test_compile_missing_engine(
        self,
        db_session: AsyncSession,
        sample_job: JobPosting,
        tmp_storage_dir: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Missing LaTeX engine on PATH marks the document as 'failed'."""
        templates_root = tmp_storage_dir / "templates"
        cv_dir = templates_root / "cv"
        cv_dir.mkdir(parents=True, exist_ok=True)
        tex_file = cv_dir / "moderncv.tex"
        tex_file.write_text("\\documentclass{article}\n\\begin{document}\nHello\n\\end{document}")

        import asyncio

        def _raise_filenotfound(*args, **kwargs):
            raise FileNotFoundError("pdflatex not found")

        monkeypatch.setattr(document_service.asyncio, "create_subprocess_exec", _raise_filenotfound)

        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir), \
             patch.object(document_service, "_templates_root", return_value=templates_root):
            payload = DocumentGenerateRequest(
                job_posting_id=sample_job.id,
                document_type="cv",
                template_name="moderncv",
            )
            doc_result = await document_service.generate_document(db_session, payload)
            result = await document_service.compile_latex(doc_result.id, db_session)

        assert result.success is False
        doc = await db_session.get(Document, doc_result.id)
        assert doc is not None
        assert doc.status == "failed"
        assert "not found" in (doc.compilation_log or "").lower()


# =============================================================================
# QUERY / VERSIONING TESTS
# =============================================================================


class TestDocumentQueries:
    """Query helpers for listing and versioning."""

    @pytest.mark.asyncio
    async def test_list_document_versions(
        self, db_session: AsyncSession, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """``list_document_versions`` returns versions newest-first."""
        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir):
            for _ in range(3):
                payload = DocumentGenerateRequest(
                    job_posting_id=sample_job.id,
                    document_type="cv",
                    template_name="moderncv",
                )
                await document_service.generate_document(db_session, payload)

        versions = await document_service.list_document_versions(
            db_session, sample_job.id, "cv"
        )
        assert len(versions) == 3
        # Newest first
        assert versions[0].version == 3
        assert versions[-1].version == 1

    @pytest.mark.asyncio
    async def test_list_all_documents_paginated(
        self, db_session: AsyncSession, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """``list_all_documents`` supports pagination."""
        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir):
            for i in range(5):
                payload = DocumentGenerateRequest(
                    job_posting_id=sample_job.id,
                    document_type="cv" if i % 2 == 0 else "cover_letter",
                    template_name="moderncv",
                )
                await document_service.generate_document(db_session, payload)

        items, total = await document_service.list_all_documents(
            db_session, page=1, per_page=2
        )
        assert len(items) == 2
        assert total == 5

    @pytest.mark.asyncio
    async def test_list_all_documents_filter_by_status(
        self, db_session: AsyncSession, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """Status filter narrows results."""
        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir):
            payload = DocumentGenerateRequest(
                job_posting_id=sample_job.id,
                document_type="cv",
                template_name="moderncv",
            )
            result = await document_service.generate_document(db_session, payload)

        # Manually mark one as ready
        doc = await db_session.get(Document, result.id)
        assert doc is not None
        doc.status = "ready"
        await db_session.commit()

        items, total = await document_service.list_all_documents(
            db_session, page=1, per_page=20, status_filter="ready"
        )
        assert total == 1
        assert items[0].status == "ready"

    @pytest.mark.asyncio
    async def test_delete_document_removes_files(
        self, db_session: AsyncSession, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """Deleting a document cleans up filesystem artifacts."""
        with patch.object(document_service, "_storage_root", return_value=tmp_storage_dir):
            payload = DocumentGenerateRequest(
                job_posting_id=sample_job.id,
                document_type="cv",
                template_name="moderncv",
            )
            result = await document_service.generate_document(db_session, payload)

        # Simulate compiled files
        doc = await db_session.get(Document, result.id)
        assert doc is not None
        pdf_path = tmp_storage_dir / "fake.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 fake")
        doc.pdf_path = str(pdf_path)
        doc.tex_path = str(tmp_storage_dir / "fake.tex")
        Path(doc.tex_path).write_text("\\fake")
        await db_session.commit()

        deleted = await document_service.delete_document(db_session, result.id)
        assert deleted is True

        # Verify DB record gone
        doc = await db_session.get(Document, result.id)
        assert doc is None

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, db_session: AsyncSession) -> None:
        """Deleting a non-existent document returns False."""
        result = await document_service.delete_document(db_session, 99999)
        assert result is False


# =============================================================================
# HTTP API TESTS (client)
# =============================================================================


class TestDocumentsHttp:
    """HTTP endpoint tests for the documents API."""

    @pytest.mark.asyncio
    async def test_generate_endpoint_returns_202(
        self, client: AsyncClient, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """POST /generate returns 202 Accepted with document ID."""
        payload = {
            "job_posting_id": sample_job.id,
            "document_type": "cv",
            "template_name": "moderncv",
        }
        response = await client.post("/api/v1/documents/generate", json=payload)
        assert response.status_code == 202
        body = response.json()
        assert body["id"] > 0
        assert body["status"] == "pending"

    @pytest.mark.asyncio
    async def test_generate_endpoint_invalid_type(
        self, client: AsyncClient, sample_job: JobPosting
    ) -> None:
        """Invalid document_type returns 422."""
        payload = {
            "job_posting_id": sample_job.id,
            "document_type": "invalid_type",
            "template_name": "moderncv",
        }
        response = await client.post("/api/v1/documents/generate", json=payload)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_document_endpoint(
        self, client: AsyncClient, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """GET /documents/{id} returns document metadata."""
        payload = {
            "job_posting_id": sample_job.id,
            "document_type": "cv",
            "template_name": "moderncv",
        }
        gen_resp = await client.post("/api/v1/documents/generate", json=payload)
        doc_id = gen_resp.json()["id"]

        response = await client.get(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == doc_id
        assert body["document_type"] == "cv"

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, client: AsyncClient) -> None:
        """GET /documents/{id} returns 404 for missing document."""
        response = await client.get("/api/v1/documents/99999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_document_status_endpoint(
        self, client: AsyncClient, sample_job: JobPosting, tmp_storage_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """GET /documents/{id}/status returns lightweight status."""
        # Mock compile_latex so the background task doesn't fail
        async def _mock_compile(doc_id, db):
            from app.schemas.document import DocumentCompileResult
            return DocumentCompileResult(success=True)

        monkeypatch.setattr(document_service, "compile_latex", _mock_compile)

        payload = {
            "job_posting_id": sample_job.id,
            "document_type": "cv",
            "template_name": "moderncv",
        }
        gen_resp = await client.post("/api/v1/documents/generate", json=payload)
        doc_id = gen_resp.json()["id"]

        response = await client.get(f"/api/v1/documents/{doc_id}/status")
        assert response.status_code == 200
        body = response.json()
        # Status should be pending or ready depending on background task timing
        assert body["status"] in ("pending", "ready", "compiling")

    @pytest.mark.asyncio
    async def test_list_versions_endpoint(
        self, client: AsyncClient, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """GET /versions returns all versions for a document type."""
        for _ in range(2):
            payload = {
                "job_posting_id": sample_job.id,
                "document_type": "cv",
                "template_name": "moderncv",
            }
            await client.post("/api/v1/documents/generate", json=payload)

        response = await client.get(
            "/api/v1/documents/versions",
            params={"job_posting_id": sample_job.id, "document_type": "cv"},
        )
        assert response.status_code == 200
        body = response.json()
        assert len(body["versions"]) == 2

    @pytest.mark.asyncio
    async def test_delete_document_endpoint(
        self, client: AsyncClient, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """DELETE /documents/{id} removes the document."""
        payload = {
            "job_posting_id": sample_job.id,
            "document_type": "cv",
            "template_name": "moderncv",
        }
        gen_resp = await client.post("/api/v1/documents/generate", json=payload)
        doc_id = gen_resp.json()["id"]

        response = await client.delete(f"/api/v1/documents/{doc_id}")
        assert response.status_code == 200

        # Confirm deleted
        get_resp = await client.get(f"/api/v1/documents/{doc_id}")
        assert get_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_download_endpoint_not_ready(
        self, client: AsyncClient, sample_job: JobPosting, tmp_storage_dir: Path
    ) -> None:
        """Downloading a document that isn't ready returns 409."""
        payload = {
            "job_posting_id": sample_job.id,
            "document_type": "cv",
            "template_name": "moderncv",
        }
        gen_resp = await client.post("/api/v1/documents/generate", json=payload)
        doc_id = gen_resp.json()["id"]

        response = await client.get(f"/api/v1/documents/{doc_id}/download")
        assert response.status_code == 409
