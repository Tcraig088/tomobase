from tomobase.registrations.base import ItemDict, Item
from tomobase.log import logger
from colorama import Fore, Style, init
init(autoreset=True)

class TransformItem(Item):
    def __init__(self, value, name):
        super().__init__(value, name)
        self._categories = {}
        
    @property
    def categories(self):
        return self._categories

    def build_heierarchy(self, hierarchy):  
        self._add_to_hierarchy(self._categories, hierarchy)

    def _add_to_hierarchy(self, current_dict, hierarchy):
        if len(hierarchy) == 0:
            return #TODO Fix bug this should never happen
        key = hierarchy[0]
        hierarchy.pop(0)
        if len(hierarchy) == 0:
            current_dict[key] = key
        else:
            if key not in current_dict:
                current_dict[key] = {}
            self._add_to_hierarchy(current_dict[key], hierarchy)


class TransformItemDict(ItemDict):
    def __init__(self, **kwargs):
        super().__init__(item_class = TransformItem, **kwargs)


    def _iterative_help(self, item, tabs=[], msg=""):
        for key, value in item.items():
            tab_str =''
            for tab in tabs:
                tab_str += tab
            msg += f"{tab_str}{key}\n"
            if isinstance(value, dict):
                tabs.append("\t")
                msg = self._iterative_help(value, tabs=tabs, msg=msg)
        return msg


    def help(self):
        msg = "\nAvailable transforms:\n"
        for key, value in self._dict.items():
            msg += f"\n{Fore.BLUE}Name: {value.name} ID: {value.value}{Style.RESET_ALL}\n"
            for subkey, subvalue in value.categories.items():
                if isinstance(subvalue, dict):
                    msg += f"{Fore.GREEN}{subkey}{Style.RESET_ALL}\n"
                    msg += self._iterative_help(subvalue, tabs=["\t"])
                else:
                    msg += f"{subkey}\n"
                
        logger.info(msg)
        
TOMOBASE_TRANSFORM_CATEGORIES = TransformItemDict( Image_Processing=None, Align=None, Project=None, Reconstruct=None, Deform=None, Quantification=None )