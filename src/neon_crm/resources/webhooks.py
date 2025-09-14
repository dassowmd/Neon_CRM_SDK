"""Webhooks resource for the Neon CRM SDK."""

from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional

from .base import BaseResource

if TYPE_CHECKING:
    from ..client import NeonClient


class WebhooksResource(BaseResource):
    """Resource for managing webhooks."""

    def __init__(self, client: "NeonClient") -> None:
        """Initialize the webhooks resource."""
        super().__init__(client, "/webhooks")

    def list(
        self,
        current_page: int = 0,
        page_size: int = 50,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        **kwargs: Any,
    ) -> Iterator[Dict[str, Any]]:
        """List webhooks with optional filtering.

        Args:
            current_page: Page number to start from (0-indexed)
            page_size: Number of items per page
            event_type: Filter by event type
            status: Filter by status (active, inactive)
            **kwargs: Additional query parameters

        Yields:
            Individual webhook dictionaries
        """
        params = {}
        if event_type is not None:
            params["eventType"] = event_type
        if status is not None:
            params["status"] = status

        params.update(kwargs)

        return super().list(current_page=current_page, page_size=page_size, **params)

    def create_webhook(
        self,
        url: str,
        event_types: List[str],
        secret: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new webhook.

        Args:
            url: The webhook URL to call
            event_types: List of event types to subscribe to
            secret: Optional secret for webhook verification
            description: Optional description of the webhook

        Returns:
            The created webhook data
        """
        data = {
            "url": url,
            "eventTypes": event_types,
        }
        if secret is not None:
            data["secret"] = secret
        if description is not None:
            data["description"] = description

        return self.create(data)

    def update_webhook(
        self,
        webhook_id: int,
        url: Optional[str] = None,
        event_types: Optional[List[str]] = None,
        secret: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an existing webhook.

        Args:
            webhook_id: The webhook ID
            url: The webhook URL to call
            event_types: List of event types to subscribe to
            secret: Optional secret for webhook verification
            description: Optional description of the webhook
            status: Webhook status (active, inactive)

        Returns:
            The updated webhook data
        """
        data = {}
        if url is not None:
            data["url"] = url
        if event_types is not None:
            data["eventTypes"] = event_types
        if secret is not None:
            data["secret"] = secret
        if description is not None:
            data["description"] = description
        if status is not None:
            data["status"] = status

        return self.update(webhook_id, data)

    def test_webhook(self, webhook_id: int) -> Dict[str, Any]:
        """Test a webhook by sending a test event.

        Args:
            webhook_id: The webhook ID to test

        Returns:
            The test result
        """
        url = self._build_url(f"{webhook_id}/test")
        return self._client.post(url)

    def get_event_types(self) -> List[Dict[str, Any]]:
        """Get available webhook event types.

        Returns:
            List of available event types
        """
        url = self._build_url("eventTypes")
        response = self._client.get(url)

        if isinstance(response, list):
            return response
        elif "eventTypes" in response:
            return response["eventTypes"]
        else:
            return []
