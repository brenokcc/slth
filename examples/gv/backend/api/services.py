import os
import sys
import time
from openai import OpenAI

OPENAI_KEY = os.getenv('OPENAI_KEY')

if 'integration_test' in sys.argv:
    OPENAI_KEY = None

if os.path.exists('/Users/breno'):
    OPENAI_KEY = None


class OpenAIService:

    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_KEY or '')

    def create_assistant(self, name):
        if OPENAI_KEY is None: return '999'
        return self.client.beta.assistants.create(
            name=name, instructions="", model="gpt-4-1106-preview"
        ).id

    def create_file(self, name, assistant_id, file_path):
        if OPENAI_KEY is None: return '999'
        vector_store = self.client.beta.vector_stores.create(name=name)
        file_streams = [open(path, "rb") for path in [file_path]]
        file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(vector_store_id=vector_store.id, files=file_streams)
        print(file_batch.status)
        print(file_batch.file_counts)
        time.sleep(5)
        self.client.beta.assistants.update(
            assistant_id, tools=[{'type': 'file_search'}],
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}}
        )
        return self.client.beta.vector_stores.files.list(vector_store.id).data[0].id

    def delete_file(self, assistant_id, file_id):
        if OPENAI_KEY is None: return '999'
        self.client.beta.assistants.files.delete(
            file_id=file_id, assistant_id=assistant_id
        )
        self.client.files.delete(file_id)

    def ask_question(self, question, assistant_id, file_ids):
        if OPENAI_KEY is None: return 'Resposta teste.'
        attachments = []
        for file_id in file_ids:
            attachments.append({ "file_id": file_id, "tools": [{"type": "file_search"}] })
        thread = self.client.beta.threads.create(messages=[{"role": "user", "content": question, "attachments": attachments,}])
        run = self.client.beta.threads.runs.create_and_poll(thread_id=thread.id, assistant_id=assistant_id)
        for i in range(1, 5):
            print('Waiting for the response...')
            time.sleep(2)
            if self.client.beta.threads.runs.retrieve(run.id, thread_id=thread.id).status == 'completed':
                break
        messages = list(self.client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
        return messages[0].content[0].text.value
