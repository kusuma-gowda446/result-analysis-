from app.database.connection import get_db, is_mongo

class SubjectModel:
    @staticmethod
    def get_all():
        db = get_db()
        if is_mongo(db):
            return list(db.subjects.find().sort([('display_order', 1), ('id', 1)]))
        return db.execute("SELECT * FROM subjects ORDER BY display_order, id").fetchall()

    @staticmethod
    def get_by_id(subject_id):
        db = get_db()
        if is_mongo(db):
            return db.subjects.find_one({'id': int(subject_id)})
        return db.execute("SELECT * FROM subjects WHERE id=?", (subject_id,)).fetchone()

    @staticmethod
    def create(name, max_marks=15, display_order=0):
        db = get_db()
        if is_mongo(db):
            next_id = 1
            max_doc = db.subjects.find_one(sort=[('id', -1)])
            if max_doc and 'id' in max_doc:
                next_id = max_doc['id'] + 1
            db.subjects.insert_one({
                'id': next_id,
                'name': name,
                'max_marks': float(max_marks),
                'display_order': int(display_order)
            })
            return
        db.execute("INSERT INTO subjects (name, max_marks, display_order) VALUES (?,?,?)",
                     (name, max_marks, display_order))
        db.commit()

    @staticmethod
    def update(subject_id, name, max_marks, display_order):
        db = get_db()
        if is_mongo(db):
            db.subjects.update_one({'id': int(subject_id)}, {'$set': {
                'name': name,
                'max_marks': float(max_marks),
                'display_order': int(display_order)
            }})
            return
        db.execute("UPDATE subjects SET name=?, max_marks=?, display_order=? WHERE id=?",
                     (name, max_marks, display_order, subject_id))
        db.commit()

    @staticmethod
    def delete(subject_id):
        db = get_db()
        if is_mongo(db):
            sub = db.subjects.find_one({'id': int(subject_id)})
            if sub:
                db.subjects.delete_one({'id': int(subject_id)})
                db.student_marks.delete_many({'subject_id': int(subject_id)})
            return sub
        sub = db.execute("SELECT name FROM subjects WHERE id=?", (subject_id,)).fetchone()
        if sub:
            db.execute("DELETE FROM subjects WHERE id=?", (subject_id,))
            db.commit()
        return sub

    @staticmethod
    def count():
        db = get_db()
        if is_mongo(db):
            return db.subjects.count_documents({})
        return db.execute("SELECT COUNT(*) FROM subjects").fetchone()[0]
