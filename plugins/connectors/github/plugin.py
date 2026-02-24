from core.connectors.github_connector import GitHubConnector


class GitHubConnectorPlugin:
    def __init__(self, config=None):
        cfg = config or {}
        self._impl = GitHubConnector(
            repo=cfg.get("repo", ""),
            token=cfg.get("token"),
            branch=cfg.get("branch"),
            include_files=cfg.get("include_files", True),
            include_issues=cfg.get("include_issues", True),
            include_pull_requests=cfg.get("include_pull_requests", True),
            include_wiki=cfg.get("include_wiki", False),
        )

    async def pull(self):
        return await self._impl.pull()

    async def test_connection(self):
        return await self._impl.test_connection()
