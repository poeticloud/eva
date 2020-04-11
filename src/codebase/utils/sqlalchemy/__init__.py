# pylint: disable=W0511,C0111,C0103
"""SQLAlchemy Help Method
"""

import time

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import OperationalError, InterfaceError, ProgrammingError

from haomo.conf import settings


ORMBase = declarative_base()


class DBC:
    """DB Connection

    http://docs.sqlalchemy.org/en/latest/orm/contextual.html
    http://docs.sqlalchemy.org/en/latest/orm/session_basics.html#session-faq-whentocreate
    """

    def __init__(self):
        self.db_uri = settings.DB_URI
        self.engine = create_engine(self.db_uri, echo=False)
        session_factory = sessionmaker(bind=self.engine)
        self.session = scoped_session(session_factory)

    def create_all(self):
        # TODO: session.remove() 保证不会死锁
        self.session.remove()
        ORMBase.metadata.create_all(self.engine)

    def drop_all(self):
        # TODO: session.remove() 保证不会死锁
        self.session.remove()
        ORMBase.metadata.drop_all(self.engine)

    def wait_for_it(self):
        """wait postgres is online
        """
        while True:
            try:
                self.engine.execute('SELECT 1')
                break
            except (OperationalError, InterfaceError, ProgrammingError) as e:
                # InterfaceError 是 db 还没启动，拒绝连接的异常
                # ProgrammingError the database system is starting up
                time.sleep(1)
                print(f"Wait database ({settings.DB_URI}) is online: {e}")


dbc = DBC()
