"""Offline regression tests; no LocalNet, wallet, or node is required."""
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from valar_daemon.PartkeyManager import (
    PartkeyManager,
    PARTKEY_GENERATION_REQUEST_OK_ADDED,
    PARTKEY_GENERATION_REQUEST_FAIL_IN_PENDING,
    PARTKEY_GENERATION_REQUEST_FAIL_PENDING_FULL,
    PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL,
)


class GeneratedBufferCapacityTests(unittest.TestCase):
    def setUp(self):
        algod = Mock()
        algod.status.return_value = {"last-round": 100}
        self.manager = PartkeyManager(
            Mock(), SimpleNamespace(client=SimpleNamespace(algod=algod))
        )

    def fill_generated(self, count):
        for index in range(count):
            self.manager.buffer_generated.add_partkey_to_buffer(
                address=f"existing-{index}", vote_first_valid=1, vote_last_valid=1000
            )

    def request(self, address="new"):
        return self.manager.add_partkey_generation_request(address, 101, 900)

    def test_accepts_new_request_after_fifty_generated_keys(self):
        self.fill_generated(50)
        before = list(self.manager.buffer_generated.partkeys)
        self.assertEqual(self.request(), PARTKEY_GENERATION_REQUEST_OK_ADDED)
        self.assertEqual(self.manager.buffer_generated.partkeys, before)
        self.assertEqual(len(self.manager.buffer_pending.partkeys), 1)
        self.assertEqual(self.request(), PARTKEY_GENERATION_REQUEST_FAIL_IN_PENDING)

    def test_pending_queue_still_rejects_work_at_fifty(self):
        for index in range(50):
            self.assertEqual(self.request(f"pending-{index}"), PARTKEY_GENERATION_REQUEST_OK_ADDED)
        self.assertEqual(self.request(), PARTKEY_GENERATION_REQUEST_FAIL_PENDING_FULL)

    def test_generated_buffer_remains_bounded(self):
        self.fill_generated(256)
        self.assertEqual(self.request(), PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL)
        self.assertEqual(len(self.manager.buffer_generated.partkeys), 256)
        with self.assertRaises(RuntimeError):
            self.fill_generated(1)


if __name__ == "__main__":
    unittest.main()
