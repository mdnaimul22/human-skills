class PaymentProcessor:
    def __init__(self):
        self.callback = self._on_payment_success

    def process(self, amount: int) -> bool:
        return self._execute_charge(amount)

    def _execute_charge(self, amount: int) -> bool:
        return amount > 0

    def _on_payment_success(self, payload: dict) -> None:
        pass

    def _obsolete_legacy_charge(self, amount: int) -> bool:
        return False
