"""KIS market repository implementation."""

from __future__ import annotations

import logging

from app.broker.interfaces.rest_client import RestClient
from app.broker.kis.api.market_api_keys import INQUIRE_ASKING_PRICE, INQUIRE_PRICE
from app.domain.market.entities.asking_price import AskingPrice
from app.domain.market.entities.stock_price import StockPrice
from app.domain.market.value_objects.symbol import Symbol
from app.dto.market.inquire_asking_price_dto import (
    InquireAskingPriceRequestDto,
    InquireAskingPriceResponseDto,
)
from app.dto.market.inquire_price_dto import InquirePriceRequestDto, InquirePriceResponseDto
from app.dto.market.mappers.asking_price_mapper import AskingPriceMapper
from app.dto.market.mappers.stock_price_mapper import StockPriceMapper
from app.repository.kis.market_api_resolver import MarketApiResolver

logger = logging.getLogger(__name__)


class KisMarketRepository:
    """Market repository backed by ``KisRestClient`` and ``ApiRegistry``."""

    def __init__(
        self,
        *,
        rest_client: RestClient,
        api_resolver: MarketApiResolver,
    ) -> None:
        """Initialize repository dependencies.

        Args:
            rest_client: KIS REST client. Direct HTTP calls are forbidden elsewhere.
            api_resolver: Registry-backed API resolver for TR ID and path lookup.
        """
        self._rest_client = rest_client
        self._api_resolver = api_resolver

    def get_current_price(self, symbol: Symbol) -> StockPrice:
        """Return current price using registry-resolved TR ID and REST client."""
        resolved = self._api_resolver.resolve(INQUIRE_PRICE)
        request = InquirePriceRequestDto(fid_input_iscd=symbol.code)
        logger.info("Fetching current price for %s via %s", symbol.code, resolved.api_key)
        result = self._rest_client.get(
            resolved.path,
            resolved.tr_id,
            params=request.to_params(),
        )
        response_dto = InquirePriceResponseDto.from_api_output(result.output)
        return StockPriceMapper.to_entity(response_dto, symbol=symbol)

    def get_asking_price(self, symbol: Symbol) -> AskingPrice:
        """Return asking price using registry-resolved TR ID and REST client."""
        resolved = self._api_resolver.resolve(INQUIRE_ASKING_PRICE)
        request = InquireAskingPriceRequestDto(fid_input_iscd=symbol.code)
        logger.info("Fetching asking price for %s via %s", symbol.code, resolved.api_key)
        result = self._rest_client.get(
            resolved.path,
            resolved.tr_id,
            params=request.to_params(),
        )
        response_dto = InquireAskingPriceResponseDto.from_api_output(result.output)
        return AskingPriceMapper.to_entity(response_dto, symbol=symbol)
