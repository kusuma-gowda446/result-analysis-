from app.utils.excel_handler import process_bulk_upload, generate_csv_template

class BulkService:
    @staticmethod
    def process_upload(file_stream, filename):
        return process_bulk_upload(file_stream, filename)

    @staticmethod
    def get_csv_template():
        return generate_csv_template()
