from PySide6.QtCore import QObject, Signal, Slot


class Worker(QObject):
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    @Slot()
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)

            if isinstance(result, str) and result.lower().startswith("error"):
                self.error.emit(result)
            else:
                self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))
