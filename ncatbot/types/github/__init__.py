"""GitHub 平台专用类型"""

from .enums import (
    GitHubAction,
    GitHubIssueState,
    GitHubMergeMethod,
    GitHubPostType,
    GitHubPRState,
    GitHubUserType,
)
from .models import (
    GitHubCommit,
    GitHubForkee,
    GitHubRelease,
    GitHubRepo,
)
from .sender import GitHubSender
from .events import (
    GitHubEventData,
    GitHubForkEventData,
    GitHubIssueCommentEventData,
    GitHubIssueEventData,
    GitHubPREventData,
    GitHubPRReviewCommentEventData,
    GitHubPushEventData,
    GitHubReleaseEventData,
    GitHubStarEventData,
)

__all__ = [
    # enums
    "GitHubPostType",
    "GitHubAction",
    "GitHubIssueState",
    "GitHubPRState",
    "GitHubUserType",
    "GitHubMergeMethod",
    # models
    "GitHubRepo",
    "GitHubCommit",
    "GitHubRelease",
    "GitHubForkee",
    # sender
    "GitHubSender",
    # events
    "GitHubEventData",
    "GitHubIssueEventData",
    "GitHubIssueCommentEventData",
    "GitHubPREventData",
    "GitHubPRReviewCommentEventData",
    "GitHubPushEventData",
    "GitHubStarEventData",
    "GitHubForkEventData",
    "GitHubReleaseEventData",
]
