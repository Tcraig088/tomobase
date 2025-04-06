from tomobase.registrations.base import ItemDict, Item

class TransformItem(Item):
    def __init__(self, value, name):
        super().__init__(value, name)
        self._categories = {}
        
    @property
    def categories(self):
        return self._categories
    
    def __setitem__(self, key, value):
        self._add_to_hierarchy(self._categories, key, value)
            
    def _add_to_hierarchy(self, current_dict, hierarchy):
        for key, value in hierarchy.items():
            if key not in current_dict:
                current_dict[key] = {}
            if isinstance(value, dict):
                self._add_to_hierarchy(current_dict[key], value)
            else:
                if isinstance(current_dict[key], list):
                    if value not in current_dict[key]:
                        current_dict[key].append(value)
                else:
                    current_dict[key] = [value]

class TransformItemDict(ItemDict):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._item_class = TransformItem
        
TOMOBASE_TRANSFORM_CATEGORIES = TransformItemDict( Deform=None, Align=None, Project=None, Reconstruct=None)