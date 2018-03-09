import schedule
import threading
import time
from gitlab_registry_usage.registry.high_level_api import GitLabRegistry


class GitLabRegistryCache:
    def __init__(self, gitlab_base_url, registry_base_url, username, password):
        self._gitlab_base_url = gitlab_base_url
        self._registry_base_url = registry_base_url
        self._username = username
        self._password = password
        self._gitlab_registry = None
        self._timestamp = None

    def update(self, run_async=False):
        def job_function():
            gitlab_registry = GitLabRegistry(
                self._gitlab_base_url, self._registry_base_url, self._username, self._password
            )
            gitlab_registry.update()
            self._gitlab_registry = gitlab_registry
            self._timestamp = time.time()

        if run_async:
            thread = threading.Thread(target=job_function)
            thread.start()
            return thread
        else:
            job_function()

    def update_continuously(self, minutes_interval=60):
        def job_function():
            while True:
                schedule.run_pending()
                time.sleep(10)

        schedule.every(minutes_interval).minutes.do(self.update)
        thread = threading.Thread(target=job_function)
        thread.start()
        return thread

    @property
    def registry(self):
        if self._gitlab_registry is None:
            self.update()
        return self._gitlab_registry

    @property
    def timestamp(self):
        return self._timestamp
