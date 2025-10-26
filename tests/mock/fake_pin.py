class FakePin:
        # Pin constants to match machine.Pin
        PULL_UP = 1

        def __init__(self, *args, **kwargs): self._val = 0
        def on(self): self._val = 1
        def off(self): self._val = 0
        def value(self): return self._val