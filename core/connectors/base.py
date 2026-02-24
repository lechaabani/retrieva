"""Base connector interface for external data sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator


@dataclass
class Document:
    """A document retrieved from an external data source."""

    content: str
    title: str
    source: str
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseConnector(ABC):
    """Abstract base class for data source connectors.

    Connectors pull documents from external systems (file systems, cloud
    storage, APIs, databases) and return them as ``Document`` instances
    ready for ingestion.
    """

    #: Human-readable connector name.
    name: str = "base"

    @abstractmethod
    async def pull(self) -> list[Document]:
        """Pull documents from the data source.

        Returns:
            A list of Document instances.

        Raises:
            ConnectorError: If the pull operation fails.
        """
        ...

    async def watch(self) -> AsyncGenerator[Document, None]:
        """Watch the data source for new or updated documents.

        Yields Document instances as they become available.
        Override in subclasses that support real-time watching.

        Raises:
            NotImplementedError: If watching is not supported.
        """
        raise NotImplementedError(f"{self.name} connector does not support watching")
        # The yield below is unreachable but required for the function
        # to be recognised as an async generator by Python.
        yield  # type: ignore[misc]  # pragma: no cover

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test whether the connector can reach the data source.

        Returns:
            True if the connection is healthy.

        Raises:
            ConnectionTestFailedError: If the test fails.
        """
        ...
