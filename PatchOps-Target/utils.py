import re
from datetime import datetime
import cache_manager
import validator
import logger
import file_manager

def sanitize_string(s):
    return re.sub(r'[^\w\s]', '', s)

def validate_email(email):
    return "@" in email

def format_date(d):
    return datetime.now().strftime("%Y-%m-%d")
