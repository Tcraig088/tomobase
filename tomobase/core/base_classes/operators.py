

class ProcedurePreview:
    def __init__(self, func, cumulative=False, **kwargs):
        self.func = func
        self.obj = obj
        self.cumulative = cumulative
        self.kwargs = kwargs
        self.working = obj.copy()

    def update(self, **kwargs):
        self.kwargs.update(kwargs)

        if not self.cumulative:
            self.working = self.obj.copy()

        self.func(self.working, **self.kwargs)
        return self.working

    def commit(self):
        self.obj.data = self.working.data
        return self.obj

    def cancel(self):
        self.working = self.obj.copy()
        return self.obj