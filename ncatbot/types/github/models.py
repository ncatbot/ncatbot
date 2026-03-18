"""GitHub 平台数据结构"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

__all__ = [
    "GitHubRepo",
    "GitHubCommit",
    "GitHubRelease",
    "GitHubForkee",
]


class GitHubRepo(BaseModel):
    """仓库信息"""

    owner: str = ""
    name: str = ""
    full_name: str = ""
    id: str = ""
    html_url: Optional[str] = None
    description: Optional[str] = None
    private: bool = False
    default_branch: Optional[str] = None


class GitHubCommit(BaseModel):
    """Commit 信息"""

    sha: str = ""
    message: str = ""
    author_name: str = ""
    author_email: str = ""
    url: Optional[str] = None
    timestamp: Optional[str] = None
    added: List[str] = Field(default_factory=list)
    removed: List[str] = Field(default_factory=list)
    modified: List[str] = Field(default_factory=list)


class GitHubRelease(BaseModel):
    """Release 信息"""

    id: str = ""
    tag_name: str = ""
    name: str = ""
    body: str = ""
    prerelease: bool = False
    draft: bool = False
    html_url: Optional[str] = None


class GitHubForkee(BaseModel):
    """Fork 目标仓库信息"""

    full_name: str = ""
    html_url: Optional[str] = None
    owner: str = ""
    description: Optional[str] = None
