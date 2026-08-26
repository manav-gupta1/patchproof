class InMemoryPublicationRecordStore:
    def __init__(self):
        self.records = {}

    def get(self, job_id):
        return self.records.get(job_id)

    def put(self, record):
        self.records[record.job_id] = record
