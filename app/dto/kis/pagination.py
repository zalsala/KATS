"""Pagination DTO for KIS REST APIs."""

from __future__ import annotations

from pydantic import BaseModel


class PaginationDto(BaseModel):
    """KIS REST pagination context fields.

    Official APIs use ``tr_cont`` plus context area fields for paged responses.

    Attributes:
        tr_cont: Continuation flag. Empty for first request, then ``F``/``M``/``D``/``E``.
        ctx_area_fk100: Forward key context area.
        ctx_area_nk100: Next key context area.
    """

    tr_cont: str = ""
    ctx_area_fk100: str = ""
    ctx_area_nk100: str = ""

    def to_params(self) -> dict[str, str]:
        """Convert pagination fields to request parameter names."""
        return {
            "CTX_AREA_FK100": self.ctx_area_fk100,
            "CTX_AREA_NK100": self.ctx_area_nk100,
        }

    def to_headers(self) -> dict[str, str]:
        """Convert pagination fields to request headers."""
        headers: dict[str, str] = {}
        if self.tr_cont:
            headers["tr_cont"] = self.tr_cont
        return headers

    def next_page(self, *, tr_cont: str, ctx_area_fk100: str, ctx_area_nk100: str) -> PaginationDto:
        """Build the next pagination DTO from a response context.

        Args:
            tr_cont: Continuation flag from response header/body.
            ctx_area_fk100: Forward key from response.
            ctx_area_nk100: Next key from response.

        Returns:
            Pagination DTO for the next request.
        """
        return PaginationDto(
            tr_cont=tr_cont,
            ctx_area_fk100=ctx_area_fk100,
            ctx_area_nk100=ctx_area_nk100,
        )

    @classmethod
    def first_page(cls) -> PaginationDto:
        """Return an empty first-page pagination DTO."""
        return cls()
