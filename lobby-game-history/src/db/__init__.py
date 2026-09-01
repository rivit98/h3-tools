import os


def get_db_url():
    connection_url = os.getenv("DATABASE_URL")
    if connection_url is None:
        raise Exception("DATABASE_URL not set")

    return connection_url.replace("postgres://", "postgresql://")