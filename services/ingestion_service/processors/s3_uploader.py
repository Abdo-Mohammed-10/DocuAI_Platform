import boto3
from botocore.exceptions import ClientError

from shared.config import settings


class S3Uploader:
    def __init__(self):
        self.client = boto3.client("s3", region_name=settings.aws_region)
        self.bucket = settings.aws_s3_bucket

    def upload_file(self, file_bytes: bytes, s3_key: str) -> str:
        try:
            self.client.put_object(
                Bucket=self.bucket,
                Key=s3_key,
                Body=file_bytes,
                ContentType="application/pdf",
            )

            return f"s3://{self.bucket}/{s3_key}"

        except ClientError as e:
            raise RuntimeError(f"Error uploading file to S3: {e}")

    def get_presigned_url(self, s3_key: str, expiry: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": s3_key},
            ExpiresIn=expiry,
        )
