from sqlalchemy import create_engine, Column, Integer, String, JSON
import os
from sqlalchemy import create_engine, event
from sqlalchemy import Column, Table, ForeignKey
from sqlalchemy import Integer, Float, String
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm import composite, relationship
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from threading import Lock
from utility.helper_functions import get_path_from_root

__PRODUCTION_DATABASE_FILE_PATH = get_path_from_root("/RDS_emulator/rds_database.db")
__TEST_DATABASE_FILE_PATH = get_path_from_root("/RDS_emulator/test.db")
hardcoded_file_path = "C:Users\\Marcu\\Desktop\\RISE drone system\\drone_interactive_map\\src\\back-end\\RDS_emulator\\test.db"
__TEST_DATABASE_FILE_PATH = hardcoded_file_path

_Base = declarative_base()


class RDSImage(_Base):
    __tablename__ = "images"

    id = Column(Integer, primary_key=True)
    coordinates = Column(JSON, unique=True)
    mode = Column(String, unique=False)
    image_path = Column(String, unique=True)
    force_que_id = Column(Integer, unique=False)

    def __init__(self, coordinates, image_path, mode, force_que_id):
        self.coordinates = coordinates
        self.image_path = image_path
        self.mode = mode
        self.force_que_id = force_que_id


class _Database:
    """A simple class used to manage thread-safe SQLAlchemy session objects."""

    def __init__(self, file_path, echo=False):
        """Database constructor.

        Sets up a new connection to a SQLite3 database file. Creates session
        factories used to create session objects.

        Keyword arguments:
        file_path   The absolute file path to the database file. If an in-memory
                    database is wanted, set this to ":memory:".
        echo        True if the engine should print SQL commands sent to the
                    DBMS, else False. (default False)
        """
        print("-----------------------SQLLITE PATH----------------------------------------")
        
        #hardcoded_file_path = "C:Users\\Marcu\\Desktop\\RISE drone system\\drone_interactive_map\\src\\back-end\\RDS_emulator\\test.db"
        #file_path = hardcoded_file_path
        self.__engine = create_engine('sqlite:///' + file_path, echo=echo)
        _Base.metadata.create_all(bind=self.__engine)
        self.__session_maker = sessionmaker(bind=self.__engine)
        self.__Session = scoped_session(self.__session_maker)

    def get_session(self):
        """Return a new thread-safe session object."""
        return self.__Session()

    def release_session(self):
        """Close and remove the session object used by the current thread."""
        return self.__Session.remove()


__active_databases = {}
__active_database_mutex = Lock()


def __get_database_instance(file_path):
    """Return a Database instance.

    This function is provided as a thread-safe means to access a Database
    instance. If a Database instance doesn't exists for the provided database
    file, a new such instance is created.

    Keyword arguments:
    file_path   The absolut file path to the SQLite3 database file.
    """

    # This is a critical section, as multiple instances of the same Database
    # might be created by different threads.
    __active_database_mutex.acquire()
    if not file_path in __active_databases.keys():
        __active_databases[file_path] = _Database(file_path)
    __active_database_mutex.release()
    return __active_databases[file_path]


__active_db = None


def use_production_db():
    """Sets the production database as the currently active database.

    Note that this setting affects all methods globally. Sessions retrieved
    using the session_scope context manager are connected to the production
    database if this setting is active.
    """
    global __active_db
    __active_db = __get_database_instance(__PRODUCTION_DATABASE_FILE_PATH)


def use_test_database_rds(in_memory=False, remove=True):
    """Sets a new test database as the currently active database.

    Note that this setting affects all methods globally. Sessions retrieved
    using the session_scope context manager are connected to the test
    database if this setting is active.

    Keyword arguments:
    in_memory   If True, the test database is created as an in-memory database.
                This setting should be set to False if the test involves multiple
                threads accessing the database, as in-memory database access from
                multiple threads is not supported by SQLite3.
    """
    global __active_db
    if in_memory:
        __active_db = _Database(":memory:")
    else:
        if os.path.exists(__TEST_DATABASE_FILE_PATH) and remove:
            os.remove(__TEST_DATABASE_FILE_PATH)
        __active_db = __get_database_instance(__TEST_DATABASE_FILE_PATH)


@contextmanager
def rds_session_scope():
    """Context manager for database sessions.

    Sample usage:
    with session_scope() as session:
        session.DATABASE_QUERY

    Abstracts the handling of the session object. A new thread-safe session
    is created automatically, connected to the currently active database. When
    reaching the end of the with block, the session automatically tries to
    commit all uncommited changes. If the commit fails, or an exception is
    raised while processing the queries, a rollback of all changes is
    automatically performed and the exception is escalated. Regardless of
    the success or failure to commit, the session is automatically closed and
    released to the database at the end of the with block.

    Note that ORM objects retrieved using a session are no longer usable after
    the session has been closed. All changes must thus be performed within a
    single with block, or the objects has to be queried again from the new
    session object.

    This context manager is inspired by the SQLAlchemy session tutorial:
    https://docs.sqlalchemy.org/en/13/orm/session_basics.html
    """
    session = __active_db.get_session()
    try:
        yield session
        session.commit()
    except:
        raise
    finally:
        pass
