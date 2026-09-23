"""Retained PostgreSQL practice helpers; configuration stays outside source."""
from config import connect


def create_connection():
    return connect()


if __name__ == '__main__':
    with create_connection() as connection:
        print('Connection to PostgreSQL DB successful')
