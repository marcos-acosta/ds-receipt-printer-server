from nepso import Printable, Printer


class WebhookBodyHandler:
    def __init__(self, printer: Printer):
        self.printer = printer

    def handle(self, message: dict) -> None:
        try:
            printables = self.generatePrintables(message)
            if printables:
                with self.printer as p:
                    p.execute(printables)
        except Exception as e:
            print(f"[Webhook handler] Failed to process message: {e}")

    def generatePrintables(self, message: dict) -> list[Printable] | None:
        raise NotImplementedError()
