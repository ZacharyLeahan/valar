# Valar participation-key buffer exhaustion

**Confirmed fixed on 2026-11-01:** after the change and Valar restart, the daemon submitted participation keys for a previously blocked contract. The operator subsequently confirmed that staking setup worked.

## Failure

In `valar_daemon` 0.4.0, the generated-key tracking buffer defaults to 50 entries. At capacity, `add_partkey_generation_request()` rejects new requests, causing delegation setup to time out even though the daemon is running and Algorand is synced.

```text
Generated buffer is full (50 partkeys).
Partkey generation request denied for delco with ID <contract-id>.
```

## Fix

In `src/valar_daemon/PartkeyManager.py`, increase only the generated-key buffer:

```diff
-self.buffer_generated = PartkeyBuffer()
+self.buffer_generated = PartkeyBuffer(max_num_of_keys=256)
```

Back up the installed file, apply the change, and restart only `valar-daemon.service`. Keep the pending generation queue at 50; do not delete participation keys. Delegators whose setup deadline already expired must retry.

## Validation

Three offline regression tests pass: requests succeed beyond 50 generated entries, duplicate pending requests are rejected, and both queue limits remain enforced. The original code reproduces the rejection at 50.

```bash
# From projects/valar-daemon, with runtime dependencies installed:
PYTHONPATH=src python -m unittest discover -s unit_tests -v
```

This raises a finite limit; it does not resolve stale-entry retention. Package upgrades may overwrite the local patch. Upstream should consider configurable capacity and safe reconciliation of removed keys.
