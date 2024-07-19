import json
from pathlib import Path

def confirm_continue(msg, default=True):
    confirm = input(f"{msg} {'Y/n' if default is True else 'y/N'} > ")
    if default is True:
        if confirm.lower().startswith('n'):
            return False
        else:
            return True
    else:
        if confirm.lower().startswith('y'):
            return True
        else:
            return False

class GlobalConfigs():

    def __init__(self):

        configs_path = Path(Path(__file__).parent.parent, "configs.json")
        with open(configs_path, 'r') as o:
            data = json.load(o)
        self.paths = {i: Path(data['paths'][i]).expanduser() for i in data['paths']}
        self.paths['registry-dir'] = Path(self.paths['projects-dropbox'], '.registry')
        self.paths['archive-dir'] = Path(self.paths['projects-dropbox'], '.archive')
        self.paths['aliases_file'] = Path(Path(__file__).parent.parent, ".bash_aliases")
