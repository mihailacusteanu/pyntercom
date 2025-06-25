class FakePin:
        def __init__(self, *args, **kwargs): self._val = 0
        def on(self): self._val = 1
        def off(self): self._val = 0
        def value(self): return self._val