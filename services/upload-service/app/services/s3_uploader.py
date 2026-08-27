import aiobotocore.session
import logging
import os
from app.core.config import settings

logger = logging.getLogger(__name__)

class S3Uploader:
    def __init__(self):
        self.session = aiobotocore.session.get_session()

    async def init_bucket(self):
        async with self.session.create_client(
            's3', 
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY
        ) as client:
            try:
                await client.head_bucket(Bucket=settings.S3_BUCKET_NAME)
            except client.exceptions.ClientError:
                logger.info(f"Creating bucket {settings.S3_BUCKET_NAME}")
                await client.create_bucket(Bucket=settings.S3_BUCKET_NAME)

                # Deployed static sites must be publicly readable to serve
                # traffic through Caddy, but that grant is scoped to the
                # `deployments/*` prefix only -- not the whole bucket -- so
                # any other prefix added to this bucket later stays private
                # by default.
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": "*",
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{settings.S3_BUCKET_NAME}/deployments/*"]
                        }
                    ]
                }
                import json
                await client.put_bucket_policy(Bucket=settings.S3_BUCKET_NAME, Policy=json.dumps(policy))

    async def upload_directory(self, local_dir: str, s3_prefix: str):
        """Uploads a local directory to S3 recursively."""
        async with self.session.create_client(
            's3', 
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY
        ) as client:
            
            for root, _, files in os.walk(local_dir):
                for file in files:
                    local_path = os.path.join(root, file)
                    # Calculate relative path to maintain directory structure
                    rel_path = os.path.relpath(local_path, local_dir)
                    s3_key = f"{s3_prefix}/{rel_path}".replace('\\', '/')
                    
                    with open(local_path, 'rb') as data:
                        await client.put_object(
                            Bucket=settings.S3_BUCKET_NAME,
                            Key=s3_key,
                            Body=data
                        )
            logger.info(f"Successfully uploaded {local_dir} to s3://{settings.S3_BUCKET_NAME}/{s3_prefix}")

s3_uploader = S3Uploader()
