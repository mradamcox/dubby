import json
from pathlib import Path


def confirm_continue(msg, default=True):
    confirm = input(f"{msg} {'Y/n' if default is True else 'y/N'} > ")
    if default is True:
        if confirm.lower().startswith("n"):
            return False
        else:
            return True
    else:
        if confirm.lower().startswith("y"):
            return True
        else:
            return False


def print_table(table):
    """From https://stackoverflow.com/a/52247284"""
    longest_cols = [
        (max([len(str(row[i])) for row in table]) + 2) for i in range(len(table[0]))
    ]
    row_format = "".join(
        ["{:<" + str(longest_col) + "}" for longest_col in longest_cols]
    )
    for row in table:
        print(row_format.format(*row))


class GlobalConfigs:
    def __init__(self):

        configs_path = Path(Path(__file__).parent.parent, "configs.json")
        with open(configs_path, "r") as o:
            configs = json.load(o)
        configs_local_path = Path(Path(__file__).parent.parent, "configs.local.json")
        if configs_local_path.is_file():
            with open(configs_local_path, "r") as o:
                configs_local = json.load(o)
            configs['paths'].update(configs_local['paths'])

        self.paths = {i: Path(configs["paths"][i]).expanduser() for i in configs["paths"]}

        ## set some more paths that are derived from base configs
        self.paths["registry-dir"] = Path(self.paths["projects-dropbox"], ".registry")
        self.paths["archive-dir"] = Path(self.paths["projects-dropbox"], ".archive")
        self.paths["aliases_file"] = Path(Path(__file__).parent.parent, ".bash_aliases")
