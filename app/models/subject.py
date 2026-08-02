from app.database.connection import get_db

class SubjectModel:
    @staticmethod
    def get_all():
        db = get_db()
        return list(db.subjects.find().sort([('display_order', 1), ('id', 1)]))

    @staticmethod
    def get_by_id(subject_id):
        db = get_db()
        return db.subjects.find_one({'id': int(subject_id)})

    @staticmethod
    def create(name, max_marks=15, display_order=0):
        db = get_db()
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

    @staticmethod
    def update(subject_id, name, max_marks, display_order):
        db = get_db()
        db.subjects.update_one({'id': int(subject_id)}, {'$set': {
            'name': name,
            'max_marks': float(max_marks),
            'display_order': int(display_order)
        }})

    @staticmethod
    def delete(subject_id):
        db = get_db()
        sub = db.subjects.find_one({'id': int(subject_id)})
        if sub:
            db.subjects.delete_one({'id': int(subject_id)})
            db.marks.delete_many({'subject_id': int(subject_id)})
        return sub

    @staticmethod
    def count():
        db = get_db()
        return db.subjects.count_documents({})
