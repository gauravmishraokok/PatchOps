import json, boto3, uuid
from datetime import datetime

dynamo = boto3.resource("dynamodb", region_name="eu-north-1")
table = dynamo.Table("breachloop_pipeline")

def lambda_handler(event, context):
    try:
        body = event.get("body")

        if isinstance(body, str):
            body = json.loads(body)
        elif body is None:
            body = event

        run_id = str(uuid.uuid4())

        item = {
            "run_id": run_id,
            "status": "RECEIVED",
            "timestamp": datetime.utcnow().isoformat(),
            "input": body
        }

        table.put_item(Item=item)

        return {
            "statusCode": 200,
            "body": json.dumps({"run_id": run_id, "status": "RECEIVED"})
        }

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
