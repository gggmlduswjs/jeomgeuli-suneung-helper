import tempfile
from pathlib import Path

import pytest

from app.infrastructure.pdf.parsers.template_manager import TemplateManager
import app.routers.templates as templates_router
import asyncio


def _fake_template_dict(subject: str, name: str, version: str) -> dict:
    return {
        "name": name,
        "subject": subject,
        "version": version,
        "description": "generated",
        "patterns": {
            "lecture_title_patterns": [r"^\d+강\s*\|\s*.+$"],
            "toc_lecture_patterns": [r"^\d+강\s*\|\s*.+$"],
            "concept_title_patterns": [],
            "content_header_patterns": [],
            "section_title_patterns": [],
            "problem_number_pattern": r"^\d{2}$",
        },
        "config": {"toc_end_page": 7, "start_content_page": 8, "paragraph_y_threshold": 25},
        "confidence": 0.85,
        "sample_texts": ["1강 | 테스트"],
        "created_at": None,
        "updated_at": None,
        "_notes": ["ok"],
    }


def test_generate_from_toc_preview(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir) / "templates"
        manager = TemplateManager(template_dir=template_dir)

        monkeypatch.setenv("OPENAI_API_KEY", "test")
        monkeypatch.setattr(templates_router, "check_openai_available", lambda: True)
        monkeypatch.setattr(
            templates_router,
            "_generate_template_from_toc_via_openai",
            lambda **kwargs: _fake_template_dict(kwargs["subject"], kwargs["name"], kwargs["version"]),
        )

        req = templates_router.GenerateTemplateFromTOCRequest(
            subject="literature",
            name="ebs_수능특강_literature_2026",
            version="2026",
            description="",
            toc_text="1강 | 시의 표현과 형식\n2강 | 시의 내용\n01\n02",
            save=False,
        )
        payload = asyncio.run(templates_router.generate_template_from_toc(req=req, manager=manager))
        assert payload["ok"] is True
        assert payload["saved"] is False
        assert payload["template"]["name"] == "ebs_수능특강_literature_2026"
        assert payload["template"]["subject"] == "literature"

        # preview는 파일 저장하지 않음
        assert not any(template_dir.glob("*.json"))


def test_generate_from_toc_save_writes_file(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        template_dir = Path(tmpdir) / "templates"
        manager = TemplateManager(template_dir=template_dir)

        monkeypatch.setenv("OPENAI_API_KEY", "test")
        monkeypatch.setattr(templates_router, "check_openai_available", lambda: True)
        monkeypatch.setattr(
            templates_router,
            "_generate_template_from_toc_via_openai",
            lambda **kwargs: _fake_template_dict(kwargs["subject"], kwargs["name"], kwargs["version"]),
        )

        req = templates_router.GenerateTemplateFromTOCRequest(
            subject="literature",
            name="ebs_수능특강_literature_2026",
            version="2026",
            description="",
            toc_text="1강 | 시의 표현과 형식\n2강 | 시의 내용\n01\n02",
            save=True,
        )
        payload = asyncio.run(templates_router.generate_template_from_toc(req=req, manager=manager))
        assert payload["ok"] is True
        assert payload["saved"] is True
        assert payload["file_path"]

        # 파일이 실제로 만들어졌는지 확인
        files = list(template_dir.glob("*.json"))
        assert len(files) == 1

        # 저장된 템플릿이 매칭 가능한지 확인
        match = manager.match_template(
            pdf_text="1강 | 시의 표현과 형식\n01\n02",
            subject="literature",
            threshold=0.1,
        )
        assert match is not None

