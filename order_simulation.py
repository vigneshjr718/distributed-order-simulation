from dataclasses import dataclass, field
from typing import Dict, Set


@dataclass(frozen=True)
class Event:
    order_id: str
    version: int
    status: str


@dataclass
class OrderState:
    order_id: str
    status: str = "CREATED"
    next_version: int = 1
    pending: Dict[int, Event] = field(default_factory=dict)
    applied_versions: Set[int] = field(default_factory=set)

    def receive(self, event: Event) -> None:
        print(
            f"RECEIVED order={event.order_id} "
            f"version={event.version} status={event.status}"
        )

        if event.version in self.applied_versions:
            print(f"  IGNORED: duplicate version {event.version}")
            return

        if event.version < self.next_version:
            print(f"  IGNORED: old version {event.version}")
            return

        if event.version > self.next_version:
            self.pending[event.version] = event
            missing = list(range(self.next_version, event.version))
            print(f"  PENDING: waiting for missing version(s) {missing}")
            return

        self.apply_event(event)

        while self.next_version in self.pending:
            pending_event = self.pending.pop(self.next_version)
            self.apply_event(pending_event)

    def apply_event(self, event: Event) -> None:
        old_status = self.status
        self.status = event.status
        self.applied_versions.add(event.version)
        self.next_version += 1

        print(
            f"  APPLIED: version {event.version}, "
            f"{old_status} -> {self.status}"
        )


class FencedOrderStore:
    def __init__(self) -> None:
        self.latest_token = 0
        self.orders: Dict[str, str] = {}

    def update(self, order_id: str, status: str, token: int) -> bool:
        print(
            f"WORKER UPDATE order={order_id} "
            f"status={status} token={token}"
        )

        if token < self.latest_token:
            print(
                f"  REJECTED: stale token {token}; "
                f"latest token is {self.latest_token}"
            )
            return False

        self.latest_token = token
        self.orders[order_id] = status

        print(f"  ACCEPTED: order {order_id} is now {status}")
        return True


def out_of_order_test() -> None:
    print("=== TEST 1: OUT-OF-ORDER AND DUPLICATE EVENTS ===")

    order = OrderState("ORD-100")

    events = [
        Event("ORD-100", 2, "SHIPPED"),
        Event("ORD-100", 1, "PAID"),
        Event("ORD-100", 2, "SHIPPED"),
    ]

    for event in events:
        order.receive(event)

    assert order.status == "SHIPPED"
    assert order.applied_versions == {1, 2}
    assert order.pending == {}

    print(
        f"RESULT: status={order.status}, "
        f"applied_versions={sorted(order.applied_versions)}, "
        f"pending={sorted(order.pending)}\n"
    )


def missing_event_test() -> None:
    print("=== TEST 2: MISSING EVENT ===")

    order = OrderState("ORD-200")

    order.receive(Event("ORD-200", 3, "SHIPPED"))

    assert order.status == "CREATED"
    assert order.next_version == 1
    assert sorted(order.pending) == [3]

    print(
        f"RESULT: status={order.status}, "
        f"next_expected_version={order.next_version}, "
        f"pending={sorted(order.pending)}\n"
    )


def stale_worker_test() -> None:
    print("=== TEST 3: STALE WORKER / FENCING TOKEN ===")

    store = FencedOrderStore()

    worker_a_token = 1
    worker_b_token = 2

    print(f"Worker A receives fencing token {worker_a_token}")
    print(f"Worker B receives newer fencing token {worker_b_token}")

    assert store.update("ORD-300", "PAID", worker_b_token)
    assert not store.update("ORD-300", "CREATED", worker_a_token)

    assert store.orders["ORD-300"] == "PAID"

    print(
        f"RESULT: status={store.orders['ORD-300']}, "
        f"latest_token={store.latest_token}\n"
    )


if __name__ == "__main__":
    out_of_order_test()
    missing_event_test()
    stale_worker_test()

    print("ALL TESTS PASSED")