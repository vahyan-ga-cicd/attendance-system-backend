import boto3
from app.core.config import settings

session = boto3.session.Session(
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_KEY,
    region_name=settings.AWS_REGION
)

s3 = session.client("s3")
dynamodb = session.resource("dynamodb")
client = session.client("dynamodb")

def ensure_table_exists(table_name, key_schema, attr_defs):
    try:
        client.describe_table(TableName=table_name)
        print(f"DEBUG: Table '{table_name}' already exists.")
    except client.exceptions.ResourceNotFoundException:
        print(f"AUTO-SETUP: Table '{table_name}' not found. Creating now...")
        dynamodb.create_table(
            TableName=table_name,
            KeySchema=key_schema,
            AttributeDefinitions=attr_defs,
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        print(f"AUTO-SETUP: Waiting for '{table_name}' to become ACTIVE...")
        waiter = client.get_waiter('table_exists')
        waiter.wait(TableName=table_name)
        print(f"AUTO-SETUP: Table '{table_name}' is now ACTIVE.")

# Ensure required tables exist on startup
ensure_table_exists(
    settings.EMPLOYEE_TABLE,
    [{'AttributeName': 'employee_id', 'KeyType': 'HASH'}],
    [{'AttributeName': 'employee_id', 'AttributeType': 'S'}]
)
ensure_table_exists(
    settings.ATTENDANCE_TABLE,
    [{'AttributeName': 'employee_id', 'KeyType': 'HASH'}, {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}],
    [{'AttributeName': 'employee_id', 'AttributeType': 'S'}, {'AttributeName': 'timestamp', 'AttributeType': 'S'}]
)

employee_table = dynamodb.Table(settings.EMPLOYEE_TABLE)
attendance_table = dynamodb.Table(settings.ATTENDANCE_TABLE)