import db_utils
import config

def generate_user_report(user_id):
    user = db_utils.query_user(user_id)
    return f"Report for user {user}"

def export_csv():
    return "id,name,email\n1,Alice,alice@example.com"
