"""Unit tests for KIS REST DTOs."""

from __future__ import annotations

import pytest

from app.dto.kis import (
    CommonRequestDto,
    CommonResponseDto,
    ErrorResponseDto,
    PaginationDto,
)

pytestmark = pytest.mark.unit


class TestCommonRequestDto:
    """Tests for CommonRequestDto."""

    def test_header_overrides(self) -> None:
        """Request DTO exposes header overrides."""
        request = CommonRequestDto(
            tr_id="FHKST01010100",
            hashkey="hash-1",
            tr_cont="N",
        )

        headers = request.header_overrides()

        assert headers["custtype"] == "P"
        assert headers["hashkey"] == "hash-1"
        assert headers["tr_cont"] == "N"


class TestCommonResponseDto:
    """Tests for CommonResponseDto."""

    def test_from_dict_success(self) -> None:
        """Response DTO parses official response fields."""
        response = CommonResponseDto.from_dict(
            {
                "rt_cd": "0",
                "msg_cd": "MCA00000",
                "msg1": "ok",
                "output": {"stck_prpr": "70000"},
            }
        )

        assert response.is_success is True
        assert response.primary_output()["stck_prpr"] == "70000"

    def test_all_rows_from_output1(self) -> None:
        """List rows are collected from output1."""
        response = CommonResponseDto.from_dict(
            {
                "rt_cd": "0",
                "output1": [{"pdno": "005930"}, {"pdno": "000660"}],
            }
        )

        assert len(response.all_rows()) == 2


class TestPaginationDto:
    """Tests for PaginationDto."""

    def test_first_page_defaults(self) -> None:
        """First page uses empty continuation values."""
        page = PaginationDto.first_page()

        assert page.tr_cont == ""
        assert page.ctx_area_fk100 == ""

    def test_to_params_uses_official_field_names(self) -> None:
        """Pagination params use KIS context area keys."""
        page = PaginationDto(ctx_area_fk100="fk", ctx_area_nk100="nk")

        params = page.to_params()

        assert params["CTX_AREA_FK100"] == "fk"
        assert params["CTX_AREA_NK100"] == "nk"


class TestErrorResponseDto:
    """Tests for ErrorResponseDto."""

    def test_from_dict_error(self) -> None:
        """Error DTO parses failed KIS response."""
        error = ErrorResponseDto.from_dict(
            {"rt_cd": "1", "msg_cd": "ERROR", "msg1": "invalid"},
            status_code=200,
            tr_id="FHKST01010100",
        )

        assert error.is_success is False
        assert error.to_message() == "invalid"
