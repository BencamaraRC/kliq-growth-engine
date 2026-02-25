"""S3 media upload for store images (profile photos, logos, blog thumbnails)."""

import logging
from io import BytesIO

import boto3
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def get_s3_client():
    """Create an S3 client using configured credentials."""
    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_s3_region,
    )


async def upload_image_from_url(
    image_url: str,
    s3_key: str,
    content_type: str = "image/jpeg",
) -> str | None:
    """Download an image from a URL and upload it to S3.

    Args:
        image_url: Source image URL to download.
        s3_key: S3 object key (path within the bucket).
        content_type: MIME type for the upload.

    Returns:
        S3 URL of the uploaded image, or None on failure.
    """
    if not image_url:
        return None

    try:
        # Download image
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()

        # Detect content type from response
        ct = response.headers.get("content-type", content_type)

        # Upload to S3
        s3 = get_s3_client()
        s3.upload_fileobj(
            BytesIO(response.content),
            settings.aws_s3_bucket,
            s3_key,
            ExtraArgs={"ContentType": ct, "ACL": "public-read"},
        )

        s3_url = f"https://{settings.aws_s3_bucket}.s3.{settings.aws_s3_region}.amazonaws.com/{s3_key}"
        logger.info(f"Uploaded image to S3: {s3_url}")
        return s3_url

    except Exception as e:
        logger.warning(f"Failed to upload image to S3: {e}")
        return None


async def upload_store_images(
    application_id: int,
    profile_image_url: str | None = None,
    banner_image_url: str | None = None,
) -> dict[str, str | None]:
    """Upload a coach's profile and banner images to S3.

    Uses the same path convention as the CMS:
    applications/{app_id}/profile.jpg
    applications/{app_id}/banner.jpg

    Args:
        application_id: CMS application ID.
        profile_image_url: Source URL for profile image.
        banner_image_url: Source URL for banner image.

    Returns:
        Dict with 'profile' and 'banner' S3 URLs.
    """
    results = {"profile": None, "banner": None}

    if profile_image_url:
        results["profile"] = await upload_image_from_url(
            image_url=profile_image_url,
            s3_key=f"applications/{application_id}/profile.jpg",
        )

    if banner_image_url:
        results["banner"] = await upload_image_from_url(
            image_url=banner_image_url,
            s3_key=f"applications/{application_id}/banner.jpg",
        )

    return results
