"""A repository adapter for document metadata that can be obtained from S3.

This includes metadata either included in HTML pages, or metadata files
published by site generators like Lander.
"""

from __future__ import annotations

import httpx
import pydantic
from aws_request_signer import AwsRequestSigner
from spherexlander.parsers.pipelinemodule import SpherexPipelineModuleMetadata


class MetadataError(Exception):
    def __init__(self, reason: str, handle: str, exc: Exception):
        super().__init__(f"Metadata error in {handle}: {reason}\n{str(exc)}")
        self.reason = reason
        self.handle = handle
        self.exc = exc


class Bucket:
    """Interface for an S3 bucket.

    This class uses the AWS Signature Version 4 to authenticate the GET
    requests to the bucket. See
    https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-auth-using-authorization-header.html

    Parameters
    ----------
    bucket
        Name of the S3 bucket.
    region
        The S3 bucket's region for purposes of signing requests.
    access_key_id
        The AWS access key ID with permissions for accessing objects in the S3
        bucket.
    secret_access_key
        The secret key corresponding to ``access_key_id``.
    """

    def __init__(
        self,
        *,
        bucket: str,
        region: str,
        access_key_id: str,
        secret_access_key: str,
        http_client: httpx.AsyncClient,
    ) -> None:
        self.bucket = bucket
        self.region = region
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.http_client = http_client
        self.signer = AwsRequestSigner(
            self.region, self.access_key_id, self.secret_access_key, "s3"
        )

    async def get_object(self, key: str) -> httpx.Response:
        """Send an authorized GET request for an S3 object."""
        url = f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"
        headers = self.signer.sign_with_headers("GET", url)
        request = self.http_client.build_request("GET", url, headers=headers)
        return await self.http_client.send(request)

    async def _get_lander_metadata(self, handle: str) -> httpx.Response:
        key = f"{handle.lower()}/v/__main/metadata.json"
        try:
            response = await self.get_object(key)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise MetadataError(
                "Could not get metadata object", handle=handle, exc=e
            )
        return response

    async def get_ssdc_ms_metadata(
        self, handle: str
    ) -> SpherexPipelineModuleMetadata:
        response = await self._get_lander_metadata(handle)
        try:
            metadata = SpherexPipelineModuleMetadata.parse_obj(response.json())
        except pydantic.ValidationError as e:
            raise MetadataError(
                "Could not parse metadata object", handle=handle, exc=e
            )
        return metadata
