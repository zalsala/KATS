"""KIS REST API client."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.broker.kis.auth.header_builder import HeaderBuilder
from app.broker.kis.auth.token_manager import TokenManager
from app.broker.kis.rest.api_result import ApiResult
from app.broker.kis.rest.error_mapper import ErrorMapper
from app.broker.kis.rest.http_transport import RestHttpTransport
from app.broker.kis.rest.rate_limiter import RateLimiter
from app.broker.kis.rest.request_builder import RequestBuilder, RestRequest
from app.broker.kis.rest.response_parser import ResponseParser
from app.broker.kis.rest.retry_policy import RetryPolicy
from app.config.config_models import BrokerConfig, TimeoutConfig

logger = logging.getLogger(__name__)


class KisRestClient:
    """KIS OpenAPI REST client with retry, timeout, and rate limiting."""

    def __init__(
        self,
        *,
        broker_config: BrokerConfig,
        request_builder: RequestBuilder,
        transport: RestHttpTransport,
        rate_limiter: RateLimiter,
        retry_policy: RetryPolicy,
        response_parser: ResponseParser | None = None,
        error_mapper: ErrorMapper | None = None,
    ) -> None:
        """Initialize REST client dependencies.

        Args:
            broker_config: Broker connection configuration.
            request_builder: Authenticated request builder.
            transport: HTTP transport implementation.
            rate_limiter: Request rate limiter.
            retry_policy: Retry policy for transient failures.
            response_parser: Optional response parser override.
            error_mapper: Optional error mapper override.
        """
        self._broker_config = broker_config
        self._request_builder = request_builder
        self._transport = transport
        self._rate_limiter = rate_limiter
        self._retry_policy = retry_policy
        self._response_parser = response_parser or ResponseParser()
        self._error_mapper = error_mapper or ErrorMapper()

    def get(
        self,
        path: str,
        tr_id: str,
        params: dict[str, Any] | None = None,
        *,
        raise_on_error: bool = True,
    ) -> ApiResult:
        """Execute an authenticated GET request."""
        request = self._request_builder.build_get(path, tr_id, params)
        result = self._execute(request)
        if raise_on_error:
            return self._error_mapper.raise_for_result(result)
        return result

    def post(
        self,
        path: str,
        tr_id: str,
        body: dict[str, Any] | None = None,
        *,
        hashkey: str | None = None,
        raise_on_error: bool = True,
    ) -> ApiResult:
        """Execute an authenticated POST request."""
        request = self._request_builder.build_post(path, tr_id, body, hashkey=hashkey)
        result = self._execute(request)
        if raise_on_error:
            return self._error_mapper.raise_for_result(result)
        return result

    def _execute(self, request: RestRequest) -> ApiResult:
        attempt = 0
        while True:
            self._rate_limiter.acquire()
            started = time.perf_counter()
            try:
                response = self._transport.request(
                    request.method,
                    request.url,
                    headers=request.headers,
                    body=request.body,
                    timeout_seconds=_resolve_timeout(self._broker_config.timeout),
                )
            except Exception as exc:
                mapped = self._error_mapper.map_transport_error(exc)
                if self._retry_policy.should_retry(
                    attempt,
                    method=request.method,
                    error=mapped,
                ):
                    delay = self._retry_policy.wait_before_retry(attempt)
                    logger.warning(
                        "Retrying %s %s after transport error (attempt=%s, delay=%ss)",
                        request.method,
                        request.path,
                        attempt + 1,
                        delay,
                    )
                    attempt += 1
                    continue
                raise mapped from exc

            latency_ms = (time.perf_counter() - started) * 1000
            result = self._response_parser.parse(
                response,
                method=request.method,
                path=request.path,
                tr_id=request.tr_id,
                latency_ms=latency_ms,
            )
            logger.info(
                "REST %s %s tr_id=%s status=%s rt_cd=%s latency_ms=%.2f",
                request.method,
                request.path,
                request.tr_id,
                result.status_code,
                result.rt_cd,
                result.latency_ms,
            )

            if result.success:
                return result

            if self._retry_policy.should_retry(
                attempt,
                method=request.method,
                status_code=result.status_code,
                msg_cd=result.msg_cd,
            ):
                delay = self._retry_policy.wait_before_retry(attempt)
                logger.warning(
                    "Retrying %s %s after API failure (attempt=%s, delay=%ss, msg_cd=%s)",
                    request.method,
                    request.path,
                    attempt + 1,
                    delay,
                    result.msg_cd,
                )
                attempt += 1
                continue

            return result


def _resolve_timeout(timeout: TimeoutConfig) -> float:
    """Resolve total request timeout from broker timeout config."""
    return float(max(timeout.connect, timeout.read, timeout.write))


def build_kis_rest_client(
    *,
    broker_config: BrokerConfig,
    token_manager: TokenManager,
    header_builder: HeaderBuilder,
    transport: RestHttpTransport | None = None,
    is_vts: bool = True,
) -> KisRestClient:
    """Create a configured ``KisRestClient`` instance.

    Args:
        broker_config: Broker connection configuration.
        token_manager: Access token manager.
        header_builder: Header builder for authenticated requests.
        transport: Optional HTTP transport override for tests.
        is_vts: True when using the KIS VTS/mock REST endpoint.

    Returns:
        Configured REST client.
    """
    from app.broker.kis.rest.http_transport import UrllibRestHttpTransport

    request_builder = RequestBuilder(
        base_url=broker_config.base_url,
        token_manager=token_manager,
        header_builder=header_builder,
    )
    return KisRestClient(
        broker_config=broker_config,
        request_builder=request_builder,
        transport=transport or UrllibRestHttpTransport(),
        rate_limiter=RateLimiter.from_vts_mode(is_vts=is_vts),
        retry_policy=RetryPolicy(broker_config.retry),
    )
