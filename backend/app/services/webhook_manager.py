"""Webhook management service for Unipile webhooks."""
import logging
from typing import Optional

from app.integration.unipile.client import get_unipile_client
from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def ensure_webhook_exists(webhook_name: str = "setdm_messages") -> Optional[str]:
    """
    Ensure a webhook exists in Unipile for receiving messages.
    
    Checks if a webhook with the given name already exists. If not, creates one.
    If webhook_base_url is not configured, logs a warning and skips webhook creation.
    
    Args:
        webhook_name: Name for the webhook (used to identify it)
        
    Returns:
        The webhook_id if webhook exists or was created, None if skipped
        
    Raises:
        Exception: If webhook creation fails
    """
    settings = get_settings()
    
    # Check if webhook_base_url is configured
    if not settings.webhook_base_url:
        logger.warning(
            "WEBHOOK_BASE_URL is not configured. Skipping webhook creation. "
            "Real-time message ingestion will not work until a webhook is configured."
        )
        return None
    
    client = get_unipile_client()
    webhook_url = f"{settings.webhook_base_url.rstrip('/')}/api/webhooks/unipile/messages"
    
    try:
        # List existing webhooks
        logger.info("Checking for existing webhooks...")
        webhooks_response = await client.list_webhooks()
        
        # Check if a webhook with this name and URL already exists
        for webhook in webhooks_response.items:
            if webhook.name == webhook_name or webhook.request_url == webhook_url:
                logger.info(
                    f"Webhook already exists: ID={webhook.id}, "
                    f"URL={webhook.request_url}, enabled={webhook.enabled}"
                )
                return webhook.id
        
        # Create new webhook if it doesn't exist
        logger.info(f"Creating new webhook at {webhook_url}...")
        response = await client.create_webhook(
            request_url=webhook_url,
            source="messaging",
            name=webhook_name,
            format="json",
            enabled=True,
            events=["message_received"],
        )
        
        logger.info(f"Webhook created successfully: ID={response.webhook_id}")
        return response.webhook_id
        
    except Exception as e:
        logger.error(f"Failed to ensure webhook exists: {str(e)}")
        logger.warning(
            "Application will continue, but real-time message ingestion may not work. "
            "You can manually create a webhook in the Unipile dashboard."
        )
        return None


async def delete_webhook(webhook_id: str) -> bool:
    """
    Delete a webhook from Unipile.
    
    Args:
        webhook_id: The ID of the webhook to delete
        
    Returns:
        True if deletion was successful, False otherwise
    """
    client = get_unipile_client()
    
    try:
        logger.info(f"Deleting webhook {webhook_id}...")
        await client.delete_webhook(webhook_id)
        logger.info(f"Webhook {webhook_id} deleted successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete webhook {webhook_id}: {str(e)}")
        return False


async def list_webhooks() -> list[dict]:
    """
    List all webhooks configured in Unipile.
    
    Returns:
        List of webhook dictionaries
    """
    client = get_unipile_client()
    
    try:
        response = await client.list_webhooks()
        return [
            {
                "id": webhook.id,
                "request_url": webhook.request_url,
                "source": webhook.source,
                "name": webhook.name,
                "format": webhook.format,
                "enabled": webhook.enabled,
                "events": webhook.events,
            }
            for webhook in response.items
        ]
        
    except Exception as e:
        logger.error(f"Failed to list webhooks: {str(e)}")
        return []

