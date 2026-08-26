from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass(frozen=True)
class JobMessage:
    job_id: str


class InMemoryJobQueue:
    """Reference queue with bounded worker concurrency."""

    def __init__(self, max_concurrency: int = 4) -> None:
        self._queue: asyncio.Queue[JobMessage] = asyncio.Queue()
        self._semaphore = asyncio.Semaphore(max_concurrency)

    async def enqueue(self, message: JobMessage) -> None:
        await self._queue.put(message)

    async def dequeue(self) -> JobMessage:
        return await self._queue.get()

    async def task_done(self) -> None:
        self._queue.task_done()

    async def run_worker(self, handler) -> None:
        while True:
            message = await self.dequeue()
            async with self._semaphore:
                try:
                    await handler(message)
                finally:
                    await self.task_done()
