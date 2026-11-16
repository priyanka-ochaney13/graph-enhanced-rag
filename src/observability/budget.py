import time


class BudgetExceeded(Exception):
    pass


class BudgetTracker:
    def __init__(self, max_cost_usd: float, max_latency_ms: int):
        self.max_cost = max_cost_usd
        self.max_latency = max_latency_ms
        self.cost = 0.0
        self.start = time.time()

    def add_cost(self, usd: float):
        self.cost += usd
        self.check()

    def elapsed_ms(self) -> float:
        return (time.time() - self.start) * 1000

    def check(self):
        if self.elapsed_ms() > self.max_latency:
            raise BudgetExceeded(f"Latency budget exceeded: {self.elapsed_ms():.0f}ms")
        if self.cost > self.max_cost:
            raise BudgetExceeded(f"Cost budget exceeded: ${self.cost:.6f}")

    def snapshot(self) -> dict:
        return {"cost": round(self.cost, 6), "latency_ms": round(self.elapsed_ms(), 1)}