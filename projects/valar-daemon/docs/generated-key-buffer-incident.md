# Generated-key buffer capacity incident

Title: valar_daemon 0.4.0 rejects new delegation setup at hardcoded 50-entry generated-key buffer limit

Observed on 2026-11-01, Python 3.12, Ubuntu Linux, synchronized Algorand mainnet node.

Impact: new delegations cannot obtain participation keys before their setup deadline. Daemon remains running; process-level health checks do not detect this.

Logs repeatedly show:
Generated buffer is full (50 partkeys).
Partkey generation request denied for delco with ID <redacted>.

Code: PartkeyManager initializes both buffers with PartkeyBuffer(), whose default max_num_of_keys is 50. add_partkey_generation_request rejects work when buffer_generated.is_full(). Generated entries are retained until vote-last-valid passes. delete_scheduled_partkeys deletes node keys without immediately removing corresponding generated-buffer entries. The exact runtime buffer composition has not been inspected.

Minimal reproduction: instantiate manager with mocked algod.status returning last-round 100; populate generated buffer with 50 distinct entries valid from round 1 to 1000; request a different key valid 101 to 900. Result is PARTKEY_GENERATION_REQUEST_FAIL_GENERATED_FULL (-4), regardless of available system resources.

Local mitigation: initialize only buffer_generated with PartkeyBuffer(max_num_of_keys=256). Keep pending buffer at 50. Back up source and restart only Valar. Previously rejected requests were accepted after restart. Restart also rebuilds memory state, so the live recovery alone does not isolate capacity change from restart effects; the mocked reproduction does isolate the limit.

Local source tests: original rejects at 50; patched accepts next request, preserves existing entries and pending capacity, rejects duplicate pending request, and enforces 256 generated entries.

Requested upstream review: make generated-key tracking capacity appropriate/configurable for multiple ads and renewals, reconcile tracking entries with removed keys safely, and expose actionable unhealthy status when setup cannot proceed. Increasing the limit is temporary mitigation and can be overwritten by package upgrades.

Live verification: previously rejected contract parameters were successfully submitted at 11:33:23 UTC after the 11:31:43 UTC restart. Another previously rejected contract missed its setup deadline and was reported as not submitted at 11:32:33 UTC. No delegator wallet confirmation has been performed by the operator. Algorand remained synced, services stayed active, and a scheduled post-restart heartbeat succeeded.


## Run the offline regression tests

With the daemon runtime dependencies installed, from `projects/valar-daemon`:

```bash
PYTHONPATH=src python -m unittest discover -s unit_tests -v
```

This does not exercise LocalNet or wallet confirmation. The regression test fails
on the original 50-entry initialization. The 256-entry mitigation remains finite;
configurable capacity and stale-entry reconciliation need upstream review.
