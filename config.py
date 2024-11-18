import os
from dotenv import load_dotenv

load_dotenv()


class Security:
    TOKEN = os.getenv("TOKEN")
