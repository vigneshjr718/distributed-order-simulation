# Distributed Order-Processing Simulation

This project simulates how a distributed system handles event ordering, delayed messages, duplicate events, missing events, and stale workers.

The order follows versioned states such as:

```text
CREATED → PAID → SHIPPED
```

## Requirements

- Python 3.9 or newer
- No external packages are required

## How to Run

Clone the repository:

```bash
git clone https://github.com/vigneshjr718/distributed-order-simulation.git
cd distributed-order-simulation
```

Run the program:

```bash
python3 order_simulation.py
```

On Windows, use:

```powershell
py order_simulation.py
```

To save the terminal output:

```bash
python3 order_simulation.py | tee output.txt
```

## Implementation Overview

Each order event contains:

```text
order_id
version
status
```

The program uses version numbers to ensure that order updates are processed correctly.

The program:

- Stores future events as pending when an earlier version is missing.
- Applies events only when the expected version arrives.
- Automatically applies pending events in the correct order.
- Ignores duplicate events that were already processed.
- Records missing events.
- Uses fencing tokens to reject updates from stale workers.

## Test 1: Out-of-Order and Duplicate Events

The program delivers the following events:

```text
version 2
version 1
version 2 again
```

Expected behavior:

1. Version 2 is placed in the pending list because version 1 has not arrived.
2. Version 1 changes the order from `CREATED` to `PAID`.
3. The pending version 2 is then applied, changing the order from `PAID` to `SHIPPED`.
4. The second version 2 event is identified as a duplicate and ignored.

This ensures that events are applied in the correct order even when they arrive out of order.

## Test 2: Missing Event

The program sends only version 3 while versions 1 and 2 are missing.

Expected behavior:

- The order remains in the `CREATED` state.
- Version 3 is recorded as pending.
- The program detects that versions 1 and 2 are missing.
- The order does not incorrectly jump directly to `SHIPPED`.

## Test 3: Stale Worker and Fencing Tokens

Two workers attempt to update the same order.

```text
Worker A → fencing token 1
Worker B → fencing token 2
```

Worker B has the newer fencing token and updates the order successfully.

When Worker A later tries to update the order using the older token, its update is rejected. This prevents a stale worker from overwriting a newer update.

## Sample Terminal Output

```text
=== TEST 1: OUT-OF-ORDER AND DUPLICATE EVENTS ===
RECEIVED order=ORD-100 version=2 status=SHIPPED
  PENDING: waiting for missing version(s) [1]
RECEIVED order=ORD-100 version=1 status=PAID
  APPLIED: version 1, CREATED -> PAID
  APPLIED: version 2, PAID -> SHIPPED
RECEIVED order=ORD-100 version=2 status=SHIPPED
  IGNORED: duplicate version 2
RESULT: status=SHIPPED, applied_versions=[1, 2], pending=[]

=== TEST 2: MISSING EVENT ===
RECEIVED order=ORD-200 version=3 status=SHIPPED
  PENDING: waiting for missing version(s) [1, 2]
RESULT: status=CREATED, next_expected_version=1, pending=[3]

=== TEST 3: STALE WORKER / FENCING TOKEN ===
Worker A receives fencing token 1
Worker B receives newer fencing token 2
WORKER UPDATE order=ORD-300 status=PAID token=2
  ACCEPTED: order ORD-300 is now PAID
WORKER UPDATE order=ORD-300 status=CREATED token=1
  REJECTED: stale token 1; latest token is 2
RESULT: status=PAID, latest_token=2

ALL TESTS PASSED
```

## Evidence

The file `output.txt` contains the terminal output from a successful program execution.

The output demonstrates:

- Correct processing of out-of-order events.
- Duplicate event detection.
- Missing-event detection.
- Correct final order state.
- Successful update from the newer worker.
- Rejection of the stale worker.

## Reflection

Timestamps alone are not enough to guarantee correct event ordering because clocks on different machines may not be perfectly synchronized. Network delays can cause an older event to arrive after a newer event, even if the timestamps appear to be ordered. Clock skew and clock adjustments can also make timestamps unreliable when comparing events from different workers. Version numbers, sequence numbers, or logical clocks provide a more reliable way to track event ordering in distributed systems.

## Repository Contents

```text
distributed-order-simulation/
├── order_simulation.py
├── README.md
└── output.txt
```

## Submission

Submit only the GitHub repository link.
