from app.db.database import SessionLocalMain, SessionLocalTyre

#for main database
def get_db_main():
    db = SessionLocalMain()
    try:
        yield db
    finally:
        db.close()

#for tyre database
def get_db_tyre():
    db = SessionLocalTyre()
    try:
        yield db
    finally:
        db.close()