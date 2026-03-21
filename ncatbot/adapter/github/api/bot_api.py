"""GitHubBotAPI — GitHub 平台 API 主实现

组合所有 Mixin 并实现 IGitHubAPIClient 接口。
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from ncatbot.api.github import IGitHubAPIClient
from ncatbot.utils import get_log

from .issue import IssueAPIMixin
from .comment import CommentAPIMixin
from .pr import PRAPIMixin
from .query import QueryAPIMixin
from .release import ReleaseAPIMixin

LOG = get_log("GitHubBotAPI")

_BASE_URL = "https://api.github.com"


class GitHubBotAPI(
    IssueAPIMixin,
    CommentAPIMixin,
    PRAPIMixin,
    QueryAPIMixin,
    ReleaseAPIMixin,
    IGitHubAPIClient,
):
    """GitHub 平台 IGitHubAPIClient 实现"""

    @property
    def platform(self) -> str:
        return "github"

    def __init__(self, token: str) -> None:
        self._token = token
        self._base_url = _BASE_URL
        self._client: Optional[httpx.AsyncClient] = None

    async def ensure_session(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers: Dict[str, str] = {
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
            if self._token:
                headers["Authorization"] = f"Bearer {self._token}"
            self._client = httpx.AsyncClient(
                headers=headers, follow_redirects=True, timeout=30
            )
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """统一 HTTP 请求"""
        client = await self.ensure_session()
        url = f"{self._base_url}{path}"
        resp = await client.request(method, url, **kwargs)

        # 记录速率限制
        remaining = resp.headers.get("X-RateLimit-Remaining")
        if remaining is not None and int(remaining) < 100:
            LOG.warning("GitHub API 速率限制接近: remaining=%s", remaining)

        if resp.status_code == 204:
            return None
        body = resp.json()
        if resp.status_code >= 400:
            msg = body.get("message", "") if isinstance(body, dict) else str(body)
            LOG.error(
                "GitHub API 错误: %s %s → %d %s", method, path, resp.status_code, msg
            )
            raise httpx.HTTPStatusError(
                message=msg,
                request=resp.request,
                response=resp,
            )
        return body

    async def call(self, action: str, params: Optional[dict] = None) -> Any:
        """通用 API 调用入口 — 按 action 名分派到对应方法"""
        method = getattr(self, action, None)
        if method is None:
            raise ValueError(f"未知的 API action: {action}")
        if params:
            return await method(**params)
        return await method()
