"""
This file contains help functions for managing session.
"""

from IMM.database.database import session_scope, UserSession

def get_session_id():
    """Returns the first session ID, if no session exists one will
    be created."""
    session_id = 1
    with session_scope() as session:
        if session.query(UserSession).count() == 0:
            dummy_session = UserSession(start_time=100, drone_mode="AUTO")
            session.add(dummy_session)

    with session_scope() as session:
        session_id = session.query(UserSession).first().id

    return session_id
