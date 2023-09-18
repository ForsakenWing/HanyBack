import mimetypes
import os
import os.path as op
from uuid import uuid1
from werkzeug.utils import secure_filename
import boto3, botocore


def generate_unique_filename(obj, filedata) -> str:
    first_part, second_part = op.splitext(filedata.filename)
    return secure_filename(f"{uuid1()}-{first_part}{second_part}")


s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


def upload_file_to_s3(file, acl="public-read"):
    filename = op.basename(file.name)
    mime_type, encoding = mimetypes.guess_type(filename)
    try:
        s3.upload_fileobj(
            file,
            os.getenv("AWS_BUCKET_NAME"),
            filename,
            ExtraArgs={"ContentType": mime_type},
        )

    except Exception as e:
        # This is a catch all exception, edit this part to fit your needs.
        print("Something Happened: ", e)
        return e

    # after upload file to s3 bucket, return filename of the uploaded file
    return filename


def remove_file_from_s3(file):
    response = s3.delete_object(
        Bucket=os.getenv("AWS_BUCKET_NAME"),
        Key=file,
    )
    return response
