import threading
from aiokafka import AIOKafkaProducer
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
from aiokafka.errors import KafkaConnectionError
from config import ActionEnum


class KafkaBatchLogger:
    def __init__(
            self,
            bootstrap_servers: str,
            topic: str,
            batch_size: int = 100,
            flush_interval: int = 5,
            max_retries: int = 3,
            retry_delay: int = 5
    ):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.batch_buffer: List[Dict[str, Any]] = []
        self.buffer_lock = threading.Lock()
        self.last_flush_time = datetime.now().timestamp()
        self.producer = None
        self._running = False

    def log_action(self, action: ActionEnum) -> None:
        """Add a new action to the batch buffer."""
        with self.buffer_lock:
            self.batch_buffer.append({
                'action': action.value,
                'timestamp': datetime.now().timestamp()
            })

    async def _connect_producer(self) -> None:
        """Establish connection to Kafka with retries."""
        for attempt in range(self.max_retries):
            try:
                self.producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    key_serializer=str.encode,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                await self.producer.start()
                return
            except KafkaConnectionError as e:
                if attempt == self.max_retries - 1:
                    raise
                print(f"Failed to connect to Kafka (attempt {attempt + 1}/{self.max_retries}): {e}")
                await asyncio.sleep(self.retry_delay)

    async def _send_batch(self, messages: List[Dict[str, Any]]) -> bool:
        """Send batch of messages to Kafka, each message as a separate record."""
        try:
            # Создаем список футур для отправки сообщений
            send_futures = []
            for message in messages:
                # Используем timestamp как ключ для обеспечения равномерного распределения
                key = str(int(message['timestamp'] * 1000))
                future = self.producer.send(self.topic, value=message, key=key)
                send_futures.append(future)

            # Ждем завершения отправки всех сообщений
            await asyncio.gather(*send_futures)

            # Дожидаемся подтверждения от брокера
            await self.producer.flush()
            return True

        except Exception as e:
            print(f"Failed to send batch: {e}")
            return False

    def should_flush(self) -> bool:
        """Check if the batch should be flushed based on size or time."""
        current_time = datetime.now().timestamp()
        return (
                len(self.batch_buffer) >= self.batch_size or
                current_time - self.last_flush_time >= self.flush_interval
        )

    async def _flush_buffer(self) -> None:
        """Flush the current batch buffer to Kafka."""
        with self.buffer_lock:
            if not self.batch_buffer:
                return

            messages_to_send = self.batch_buffer.copy()
            self.batch_buffer.clear()
            self.last_flush_time = datetime.now().timestamp()

        if await self._send_batch(messages_to_send):
            print(f"Successfully sent batch of {len(messages_to_send)} messages")
        else:
            # If send fails, return messages to buffer
            with self.buffer_lock:
                self.batch_buffer.extend(messages_to_send)

    async def start(self) -> None:
        """Start the batch logger."""
        if self._running:
            return

        self._running = True
        await self._connect_producer()

        while self._running:
            try:
                if self.should_flush():
                    await self._flush_buffer()
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error in batch processing loop: {e}")
                await asyncio.sleep(self.retry_delay)

    async def stop(self) -> None:
        """Stop the batch logger and flush remaining messages."""
        self._running = False
        if self.producer:
            await self._flush_buffer()
            await self.producer.stop()
