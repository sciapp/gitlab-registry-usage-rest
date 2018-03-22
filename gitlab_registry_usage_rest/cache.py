import threading
import time
from gitlab_registry_usage.registry.high_level_api import GitLabRegistry
from typing import cast, Optional


class GitLabRegistryCache:
    def __init__(self, gitlab_base_url: str, registry_base_url: str, username: str, password: str) -> None:
        self._gitlab_base_url = gitlab_base_url
        self._registry_base_url = registry_base_url
        self._username = username
        self._password = password
        self._gitlab_registry = None  # type: Optional[GitLabRegistry]
        self._timestamp = None  # type: Optional[float]

    def update(self, run_async: bool = False) -> Optional[threading.Thread]:
        def job_function() -> None:
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
            return None

    def update_continuously(self, minutes_interval: int = 60) -> threading.Thread:
        def job_function() -> None:
            time_delta = 0.0
            while True:
                start_time = time.time()
                self.update()
                time_delta = time.time() - start_time
                time.sleep(minutes_interval * 60 - time_delta)

        thread = threading.Thread(target=job_function)
        thread.start()
        return thread

    @property
    def registry(self) -> GitLabRegistry:
        if self._gitlab_registry is None:
            self.update()
        return self._gitlab_registry

    @property
    def timestamp(self) -> float:
        if self._timestamp is None:
            self.update()
        return cast(float, self._timestamp)
