from app.services.s3_service import load_json_from_s3


orders = load_json_from_s3("orders.json")

print(orders)