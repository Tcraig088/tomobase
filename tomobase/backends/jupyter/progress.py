
from ipywidgets import Label, VBox, IntProgress, HBox
from IPython.display import display 

from ...core.prog import progress, ProgressItem, ProgressMetric
from ...core import logger

class ProgressBarWidget(VBox):
    def __init__(self, name, progress_item: ProgressItem):
        super().__init__()
        self.name_label = Label(name)
        self.progress_item = progress_item
        if not progress_item._is_iteration_estimated:
            self.progress_bar = IntProgress(min=0, max=progress_item.total)
        else:
            self.progress_bar = IntProgress(min=0, max=100)
        self.eta_label = Label(self._get_eta_text())
        self.metric_label = Label(self._get_metric_text())
        
        
        self.progress_item.updated.connect(self._on_progress_updated, weak=False)
        self.progress_item.completed.connect(self._on_completed, weak=False)
        
        self.children =([self.name_label, HBox([self.progress_bar, self.eta_label]), self.metric_label])
        
        
    def _get_eta_text(self): 
        if not self.progress_item._is_iteration_estimated:
            msg = f"Iterations: {self.progress_item.i} | {self.progress_item.total} Time: {self.progress_item.time_elapsed()} | {self.progress_item.time_remaining()}" 
        else:
            msg = f"Iterations: {self.progress_item.i} Time: {self.progress_item.time_elapsed()} | {self.progress_item.time_remaining()}"
        return msg
        
    def _get_metric_text(self):
        if self.progress_item.metric is not None:
            metric = self.progress_item.metric
            if metric.value is not None:
                value = metric.value
            else:
                value = "N/A"
            return f"{metric.name}({metric.units}): {value:.4f} | Criteria: {metric.criteria:.4f}"
        else:
            return ""
        
    def _on_progress_updated(self, sender, info):
        self.progress_bar.value = self.progress_item.i
        self.progress_bar.max = self.progress_item.total
        self.eta_label.value = self._get_eta_text()
        self.metric_label.value = self._get_metric_text()
    
    def _on_completed(self, sender, bar):
        self.progress_item.updated.disconnect(self._on_progress_updated)
        self.progress_item.completed.disconnect(self._on_completed)
        self.close()
        
def _on_progress_created(sender, name, info):
    widget = ProgressBarWidget(name, info)
    display(widget)
    
progress.progress_created.connect(_on_progress_created, weak=True)



    
    