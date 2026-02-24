"""GitHub connector using the GitHub REST API v3."""

from __future__ import annotations

import base64
import logging
from pathlib import PurePosixPath
from typing import Any, Optional

from core.connectors.base import BaseConnector, Document
from core.exceptions import ConnectorError, ConnectionTestFailedError

logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com"

# File extensions we consider text-based and worth indexing.
_TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb",
    ".c", ".cpp", ".h", ".hpp", ".cs", ".swift", ".kt", ".scala",
    ".php", ".sh", ".bash", ".zsh", ".fish", ".ps1",
    ".md", ".rst", ".txt", ".csv", ".json", ".yaml", ".yml", ".toml",
    ".xml", ".html", ".htm", ".css", ".scss", ".less",
    ".sql", ".r", ".R", ".jl", ".lua", ".pl", ".pm",
    ".dockerfile", ".tf", ".hcl", ".nix", ".el", ".clj",
    ".env.example", ".gitignore", ".editorconfig",
    "Makefile", "Dockerfile", "Rakefile", "Gemfile",
}


class GitHubConnector(BaseConnector):
    """Connector for GitHub repositories via the REST API.

    Supports:
    * Fetching repository file contents (text files).
    * Fetching issues (open/closed) with comments.
    * Fetching pull requests with review comments.
    * Fetching wiki pages (if the repo has a wiki).
    * Filtering by file path patterns and branches.
    * Pagination for all list endpoints.
    """

    name = "github"

    def __init__(
        self,
        repo: str,
        token: Optional[str] = None,
        branch: Optional[str] = None,
        include_files: bool = True,
        include_issues: bool = True,
        include_pull_requests: bool = True,
        include_wiki: bool = False,
        file_extensions: Optional[list[str]] = None,
        path_prefix: Optional[str] = None,
        max_files: int = 200,
        max_issues: int = 100,
        max_prs: int = 50,
        issue_state: str = "all",
    ) -> None:
        """
        Args:
            repo: Repository in ``owner/repo`` format.
            token: GitHub personal access token or fine-grained token.
            branch: Branch to pull files from (default: repo default branch).
            include_files: Whether to pull repository file contents.
            include_issues: Whether to pull issues.
            include_pull_requests: Whether to pull pull requests.
            include_wiki: Whether to pull wiki pages.
            file_extensions: File extensions to include (default: common text files).
            path_prefix: Only include files under this path prefix.
            max_files: Maximum number of files to pull.
            max_issues: Maximum number of issues to pull.
            max_prs: Maximum number of PRs to pull.
            issue_state: State filter for issues/PRs: "open", "closed", or "all".
        """
        self.repo = repo
        self.token = token
        self.branch = branch
        self.include_files = include_files
        self.include_issues = include_issues
        self.include_pull_requests = include_pull_requests
        self.include_wiki = include_wiki
        self.file_extensions = set(file_extensions) if file_extensions else _TEXT_EXTENSIONS
        self.path_prefix = path_prefix or ""
        self.max_files = max_files
        self.max_issues = max_issues
        self.max_prs = max_prs
        self.issue_state = issue_state

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _paginated_get(
        self, client, url: str, params: Optional[dict] = None, max_items: int = 100
    ) -> list[dict[str, Any]]:
        """GET with Link-header pagination."""
        items: list[dict[str, Any]] = []
        params = dict(params or {})
        params.setdefault("per_page", min(100, max_items))

        next_url: Optional[str] = url

        while next_url and len(items) < max_items:
            resp = await client.get(next_url, headers=self._headers(), params=params)
            if resp.status_code == 409:
                # Empty repo
                return []
            resp.raise_for_status()
            data = resp.json()

            if isinstance(data, list):
                items.extend(data)
            else:
                # Some endpoints return objects with items in a key
                break

            # Parse Link header for next page
            next_url = None
            link_header = resp.headers.get("Link", "")
            for part in link_header.split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip().strip("<>")
                    params = {}  # URL already contains params
                    break

        return items[:max_items]

    # ------------------------------------------------------------------
    # File tree fetching
    # ------------------------------------------------------------------

    async def _get_tree(self, client) -> list[dict[str, Any]]:
        """Get the full file tree using the Git Trees API (recursive)."""
        ref = self.branch or "HEAD"
        url = f"{_GITHUB_API}/repos/{self.repo}/git/trees/{ref}"
        resp = await client.get(
            url,
            headers=self._headers(),
            params={"recursive": "1"},
        )
        if resp.status_code == 409:
            return []
        resp.raise_for_status()
        data = resp.json()
        return data.get("tree", [])

    async def _fetch_file_content(self, client, path: str) -> Optional[str]:
        """Fetch a file's content from the repo contents API."""
        ref_param = {"ref": self.branch} if self.branch else {}
        resp = await client.get(
            f"{_GITHUB_API}/repos/{self.repo}/contents/{path}",
            headers=self._headers(),
            params=ref_param,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        encoding = data.get("encoding", "")
        content = data.get("content", "")

        if encoding == "base64" and content:
            try:
                return base64.b64decode(content).decode("utf-8", errors="replace")
            except Exception:
                return None
        return content or None

    async def _pull_files(self, client) -> list[Document]:
        """Pull text file contents from the repository."""
        tree = await self._get_tree(client)

        # Filter to text files matching criteria
        candidates: list[str] = []
        for item in tree:
            if item.get("type") != "blob":
                continue
            path = item.get("path", "")
            if self.path_prefix and not path.startswith(self.path_prefix):
                continue

            p = PurePosixPath(path)
            ext = p.suffix.lower()
            name = p.name

            if ext in self.file_extensions or name in self.file_extensions:
                candidates.append(path)

            if len(candidates) >= self.max_files:
                break

        logger.info("GitHub: fetching %d files from %s", len(candidates), self.repo)

        documents: list[Document] = []
        for path in candidates:
            content = await self._fetch_file_content(client, path)
            if content and content.strip():
                documents.append(Document(
                    content=content,
                    title=path,
                    source=f"https://github.com/{self.repo}/blob/{self.branch or 'main'}/{path}",
                    metadata={
                        "connector": self.name,
                        "repo": self.repo,
                        "path": path,
                        "type": "file",
                    },
                ))

        return documents

    # ------------------------------------------------------------------
    # Issues
    # ------------------------------------------------------------------

    async def _pull_issues(self, client) -> list[Document]:
        """Pull GitHub issues with comments."""
        url = f"{_GITHUB_API}/repos/{self.repo}/issues"
        issues = await self._paginated_get(
            client, url,
            params={"state": self.issue_state, "sort": "updated", "direction": "desc"},
            max_items=self.max_issues,
        )

        documents: list[Document] = []
        for issue in issues:
            # Skip pull requests (they also appear in /issues)
            if issue.get("pull_request"):
                continue

            number = issue["number"]
            title = issue.get("title", "")
            body = issue.get("body", "") or ""
            state = issue.get("state", "")
            author = issue.get("user", {}).get("login", "unknown")
            labels = [l.get("name", "") for l in issue.get("labels", [])]
            created = issue.get("created_at", "")

            parts = [f"# Issue #{number}: {title}", f"State: {state}", f"Author: {author}"]
            if labels:
                parts.append(f"Labels: {', '.join(labels)}")
            parts.append(f"Created: {created}")
            parts.append("")
            parts.append(body)

            # Fetch comments
            comments_url = issue.get("comments_url", "")
            if comments_url and issue.get("comments", 0) > 0:
                try:
                    comments = await self._paginated_get(client, comments_url, max_items=50)
                    for comment in comments:
                        c_author = comment.get("user", {}).get("login", "unknown")
                        c_body = comment.get("body", "") or ""
                        c_date = comment.get("created_at", "")
                        parts.append(f"\n---\nComment by {c_author} ({c_date}):\n{c_body}")
                except Exception as exc:
                    logger.warning("Failed to fetch comments for issue #%d: %s", number, exc)

            documents.append(Document(
                content="\n".join(parts),
                title=f"Issue #{number}: {title}",
                source=issue.get("html_url", f"https://github.com/{self.repo}/issues/{number}"),
                metadata={
                    "connector": self.name,
                    "repo": self.repo,
                    "type": "issue",
                    "number": number,
                    "state": state,
                    "labels": labels,
                },
            ))

        return documents

    # ------------------------------------------------------------------
    # Pull Requests
    # ------------------------------------------------------------------

    async def _pull_prs(self, client) -> list[Document]:
        """Pull GitHub pull requests with review comments."""
        url = f"{_GITHUB_API}/repos/{self.repo}/pulls"
        prs = await self._paginated_get(
            client, url,
            params={"state": self.issue_state, "sort": "updated", "direction": "desc"},
            max_items=self.max_prs,
        )

        documents: list[Document] = []
        for pr in prs:
            number = pr["number"]
            title = pr.get("title", "")
            body = pr.get("body", "") or ""
            state = pr.get("state", "")
            author = pr.get("user", {}).get("login", "unknown")
            base_branch = pr.get("base", {}).get("ref", "")
            head_branch = pr.get("head", {}).get("ref", "")
            created = pr.get("created_at", "")
            merged = pr.get("merged_at")

            parts = [
                f"# PR #{number}: {title}",
                f"State: {state}" + (" (merged)" if merged else ""),
                f"Author: {author}",
                f"Branch: {head_branch} -> {base_branch}",
                f"Created: {created}",
                "",
                body,
            ]

            # Fetch review comments
            comments_url = pr.get("review_comments_url", "")
            if comments_url:
                try:
                    comments = await self._paginated_get(client, comments_url, max_items=50)
                    for comment in comments:
                        c_author = comment.get("user", {}).get("login", "unknown")
                        c_body = comment.get("body", "") or ""
                        c_path = comment.get("path", "")
                        parts.append(f"\n---\nReview comment by {c_author} on {c_path}:\n{c_body}")
                except Exception as exc:
                    logger.warning("Failed to fetch comments for PR #%d: %s", number, exc)

            documents.append(Document(
                content="\n".join(parts),
                title=f"PR #{number}: {title}",
                source=pr.get("html_url", f"https://github.com/{self.repo}/pull/{number}"),
                metadata={
                    "connector": self.name,
                    "repo": self.repo,
                    "type": "pull_request",
                    "number": number,
                    "state": state,
                    "merged": merged is not None,
                },
            ))

        return documents

    # ------------------------------------------------------------------
    # Wiki
    # ------------------------------------------------------------------

    async def _pull_wiki(self, client) -> list[Document]:
        """Pull wiki pages from the repo's wiki (if enabled).

        GitHub wikis are separate git repos at {repo}.wiki.git.
        We use the Contents API on the wiki repo to list pages.
        """
        wiki_repo = f"{self.repo}.wiki"
        tree_url = f"{_GITHUB_API}/repos/{wiki_repo}/git/trees/master"

        resp = await client.get(tree_url, headers=self._headers(), params={"recursive": "1"})
        if resp.status_code != 200:
            logger.debug("Wiki not available for %s (status %d)", self.repo, resp.status_code)
            return []

        tree = resp.json().get("tree", [])
        documents: list[Document] = []

        for item in tree:
            if item.get("type") != "blob":
                continue
            path = item.get("path", "")
            if not path.lower().endswith((".md", ".mediawiki", ".rdoc", ".textile", ".org", ".creole", ".pod", ".asciidoc", ".rst", ".txt")):
                continue

            content = await self._fetch_wiki_page(client, wiki_repo, path)
            if content and content.strip():
                page_name = PurePosixPath(path).stem
                documents.append(Document(
                    content=content,
                    title=f"Wiki: {page_name}",
                    source=f"https://github.com/{self.repo}/wiki/{page_name}",
                    metadata={
                        "connector": self.name,
                        "repo": self.repo,
                        "type": "wiki",
                        "wiki_path": path,
                    },
                ))

        return documents

    async def _fetch_wiki_page(self, client, wiki_repo: str, path: str) -> Optional[str]:
        """Fetch a wiki page's content."""
        resp = await client.get(
            f"{_GITHUB_API}/repos/{wiki_repo}/contents/{path}",
            headers=self._headers(),
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        if data.get("encoding") == "base64" and data.get("content"):
            try:
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            except Exception:
                return None
        return data.get("content")

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def pull(self) -> list[Document]:
        """Pull documents from a GitHub repository.

        Returns:
            List of Document instances from files, issues, PRs, and wiki.

        Raises:
            ConnectorError: On authentication or API errors.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
                documents: list[Document] = []

                if self.include_files:
                    docs = await self._pull_files(client)
                    documents.extend(docs)
                    logger.info("GitHub: pulled %d file documents", len(docs))

                if self.include_issues:
                    docs = await self._pull_issues(client)
                    documents.extend(docs)
                    logger.info("GitHub: pulled %d issue documents", len(docs))

                if self.include_pull_requests:
                    docs = await self._pull_prs(client)
                    documents.extend(docs)
                    logger.info("GitHub: pulled %d PR documents", len(docs))

                if self.include_wiki:
                    docs = await self._pull_wiki(client)
                    documents.extend(docs)
                    logger.info("GitHub: pulled %d wiki documents", len(docs))

                logger.info("GitHub: total %d documents from %s", len(documents), self.repo)
                return documents

        except ConnectorError:
            raise
        except Exception as exc:
            raise ConnectorError(f"GitHub pull failed: {exc}") from exc

    async def test_connection(self) -> bool:
        """Test connectivity by fetching repository metadata.

        Returns:
            True if the repo is accessible.

        Raises:
            ConnectionTestFailedError: If the connection test fails.
        """
        import httpx

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{_GITHUB_API}/repos/{self.repo}",
                    headers=self._headers(),
                )
                resp.raise_for_status()
                return True
        except Exception as exc:
            raise ConnectionTestFailedError(f"GitHub connection test failed: {exc}") from exc
