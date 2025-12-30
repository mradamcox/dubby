from __future__ import annotations
import os
import json
import shutil
from datetime import date
from pathlib import Path
import subprocess
from typing import Literal

from .utils import GlobalConfigs, confirm_continue

GLOBAL = GlobalConfigs()


class Project:

    def __init__(
        self,
        name: str,
        status: Literal["active", "inactive", "archived"] = "active",
        org: str = None,
        tags: list = [],
        tagline: str = None,
        description: str = None,
    ):
        self.name = name
        self.status = status
        self.org = org
        self.tags = tags
        self.tagline = tagline
        self.description = description

        self.local_path = Path(GLOBAL.paths["projects-local"], self.name)
        self.is_local = self.local_path.is_dir()

    def initialize_local(self) -> Project:
        self.local_path.mkdir(exist_ok=True)
        self.is_local = True
        print(f"project directory: {self.local_path}")

        self.sync_logseq_notes()
        print(f"new logseq page created: projects___{self.name}.md")
        print(f"  symlinked to: {self.local_path}/Notes/main.md")

        self.create_workon_script()
        print(".workon startup script created")

        self.sync_symlinks()
        print("all symlinks created")

        return self

    def sync_logseq_notes(self):
        self.create_logseq_page()
        notes_dir = Path(self.local_path, "Notes")
        notes_dir.mkdir(exist_ok=True)
        assets_dir = Path(self.local_path, "Notes", "assets")
        assets_dir.mkdir(exist_ok=True)
        logseq_pages = Path(GLOBAL.paths["logseq-notes"], "pages").glob(
            f"projects___{self.name}*.md"
        )
        logseq_assets_dir = Path(GLOBAL.paths["logseq-notes"], "assets")
        for path in logseq_pages:
            print(path)
            name_parts = path.name.split("___")
            if len(name_parts) == 2:
                link_name = "main.md"
            elif len(name_parts) == 3:
                link_name = name_parts[2]
            else:
                link_name = "___".join(name_parts[2:])

            link_path = Path(notes_dir, link_name)
            if not link_path.is_symlink():
                link_path.symlink_to(path)
            # look for any images and symlink them in as well
            with open(path, "r") as o:
                for line in o.readlines():
                    if "../assets/" in line:
                        img_name = line.split("../assets/")[1].rstrip().rstrip(")")
                        img_path = Path(logseq_assets_dir, img_name)
                        img_link_path = Path(assets_dir, img_name)
                        if img_link_path.is_symlink():
                            img_link_path.unlink()
                        img_link_path.symlink_to(img_path)

        # remove the assets dir if nothing has been put in it
        if not any(assets_dir.iterdir()):
            assets_dir.rmdir()

        # remove links to any pages that have been deleted
        for link in notes_dir.iterdir():
            if link.is_symlink():
                if not link.resolve().is_file():
                    link.unlink()

    def create_logseq_page(self):
        page_path = Path(
            GLOBAL.paths["logseq-notes"], "pages", f"projects___{self.name}.md"
        )

        if not page_path.is_file():
            day = date.today().day
            if 4 <= day <= 20 or 24 <= day <= 30:
                suffix = "th"
            else:
                suffix = ["st", "nd", "rd"][day % 10 - 1]
            day_str = f"{day}{suffix}"
            date_str = date.today().strftime(f"%h {day_str}, %Y")
            page_path.write_text(f"""created:: [[{date_str}]]
- #+BEGIN_QUERY
  {{:title [:h2 "Pages"]
   :query [:find (pull ?p [*])
    :in $ ?current
    :where
     [?c :block/name ?current]
     [?p :block/namespace ?c]
   ]
   :inputs [:query-page]
  }}
  #+END_QUERY
- ## Summary
""")

    def create_workon_script(self):
        workon_path = Path(self.local_path, ".workon")
        if not workon_path.is_file():
            with open(workon_path, "w") as f:
                f.write("#! /usr/bin/bash\n\n")
                f.write('PROJECT_DIR=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)\n')
                f.write("xdg-open $PROJECT_DIR\n")
                f.write("cd $PROJECT_DIR\n")

    def sync_symlinks(self, links: str = "all", remove: bool = False):

        if self.is_local:

            if links in ["all", "status"]:
                self.set_status_symlink(remove=remove)

            if links in ["all", "dropbox"]:
                self.set_dropbox_symlink(remove=remove)

    def set_dropbox_symlink(self, remove=False):
        dbox_projects = Path(GLOBAL.paths["projects-dropbox"])
        dbox_projects.mkdir(exist_ok=True)

        d_proj = Path(dbox_projects, self.name)

        ## TODO: this removal should be placed in a separate function
        if remove is True:
            if confirm_continue("Delete the folder in dropbox?"):
                try:
                    shutil.rmtree(d_proj)
                except Exception as e:
                    print(f"[ERROR] {e}")
        else:
            d_proj.mkdir(exist_ok=True)
            d_link = Path(self.local_path, "Dropbox")
            if d_link.is_symlink():
                d_link.unlink()
            d_link.symlink_to(d_proj)

    def copy_notes_to_dropbox(self):
        dbox_notes_path = Path(GLOBAL.paths["legion"], "project-notes")
        dbox_notes_path.mkdir(exist_ok=True)

        dbox_project_notes_dir = Path(dbox_notes_path, self.name)
        dbox_project_notes_dir.mkdir(exist_ok=True)

        local_project_notes = Path(self.local_path, "Notes")
        for md_file in local_project_notes.glob("*.md"):
            shutil.copy(md_file, Path(dbox_project_notes_dir, md_file.name))
        assets_dir = Path(local_project_notes, "assets")
        if assets_dir.is_dir():
            shutil.copytree(
                assets_dir, Path(dbox_project_notes_dir, "assets"), dirs_exist_ok=True
            )

    def set_status_symlink(self, remove=False):
        stati = ["active", "inactive", "archived"]

        links = {}
        for status in stati:
            status_dir = Path(f"{str(GLOBAL.paths['projects-local'])}--{status}")
            status_dir.mkdir(exist_ok=True)
            links[status] = Path(status_dir, self.name)

        if remove is True:
            for link in links.values():
                if link.is_symlink():
                    link.unlink()
        else:
            newlink = links[self.status]
            if not newlink.is_symlink():
                newlink.symlink_to(self.local_path)
            oldlinks = [i for i in links.values() if not i == newlink]
            for ol in oldlinks:
                if ol.is_symlink():
                    ol.unlink()

    def set_status(self, status):
        if status not in ["active", "inactive", "archived"]:
            print(f"[WARNING] Invalid status: {status} -- no change made")
            return

        self.status = status
        self.save_manifest()
        self.set_status_symlink()

    def add_tags(self, tags: list):
        self.tags += tags
        self.tags = list(set(self.tags))
        self.save_manifest()

    def remove_tags(self, tags: list):
        self.tags = [i for i in self.tags if i not in tags]
        self.save_manifest()

    def set_description(self, description: str):
        self.description = description
        self.save_manifest()

    def set_tagline(self, tagline: str):
        self.tagline = tagline
        self.save_manifest()

    def serialize(self):
        return {
            "status": self.status,
            "org": self.org,
            "tags": sorted(self.tags),
            "description": self.description,
            "tagline": self.tagline,
        }

    def backup(self, target: Path = None, exclude: "list[str]" = []):

        if not target:
            target = GLOBAL.paths["projects-local"]

        archive_name = date.today().strftime(f"{self.name}___%Y-%m-%d.tar.gz")
        archive_path = Path(target, archive_name)

        cmd = ["tar", "-C", str(self.local_path.parent)]

        exclusions = [
            "Notes",
            "Dropbox",
            "node_modules",
            "env",
            "ENV",
            "__pycache__",
        ]
        exclusions += exclude

        for ex in exclusions:
            cmd.append("--exclude")
            cmd.append(ex)

        cmd += ["-czf", str(archive_path), self.local_path.name]

        subprocess.call(cmd)

        return archive_path

    def save_manifest(self):
        manifest_dir = Path(GLOBAL.paths["registry-dir"])
        manifest_dir.mkdir(parents=True, exist_ok=True)
        data = self.serialize()

        man_path = Path(manifest_dir, self.name + ".json")
        with open(man_path, "w") as o:
            json.dump(data, o, indent=2)


class Registry:

    def get_project(self, name) -> Project:
        manifest_path = Path(GLOBAL.paths["registry-dir"], name + ".json")
        if manifest_path.is_file():
            with open(manifest_path, "r") as o:
                data = json.load(o)
            data['name'] = manifest_path.stem
            project = Project(**data)
            return project
        else:
            return None

    def get_projects(
        self,
        tags: "list[str]" = [],
        status: str = None,
        local: bool = False,
        org: str = None,
    ) -> "list[Project]":
        manifest_paths = Path(GLOBAL.paths["registry-dir"]).glob("*.json")
        projects: list[Project] = []

        for mp in sorted(manifest_paths, key=lambda path: path.stem.lower()):
            project = self.get_project(mp.stem)
            projects.append(project)

        if tags:
            projects = [i for i in projects if bool(set(i.tags).intersection(tags))]
        if status:
            projects = [i for i in projects if i.status == status]
        if local:
            projects = [i for i in projects if i.is_local]
        if org:
            projects = [i for i in projects if i.org == org]

        return projects

    def create_project(self, name: str, status="active", tags: list[str]=[], tagline: str=None, description: str=None):
        """Creates a new project in the registry and then sets up a local
        dirctory for it with all the bells and whistles in it. This is different
        from add_project in that the the project must not yet exist."""

        existing = self.get_project(name)
        if existing:
            raise Exception(f"A project by this name already exists: {name}")

        org = None
        if "__" in name:
            org = name.split("__")[0]

        entry = {
            "name": name,
            "org": org,
            "status": status,
            "tags": tags,
            "tagline": tagline,
            "description": description
        }

        project = Project(**entry)
        project.save_manifest()

        project.initialize_local()

        self.sync_aliases()
        return project

    def delete_project(self, name):
        project = self.get_project(name)

        if project:
            note_paths = [
                i for i in Path(GLOBAL.paths["logseq-notes"], "pages").glob(
                    f"projects___{name}___*.md"
                )
            ]
            note_paths.append(
                Path(GLOBAL.paths["logseq-notes"], "pages", f"projects___{name}.md")
            )
            notes = [i for i in note_paths if i.is_file()]
            if len(notes) > 0:
                print("existing Logseq notes:")
                for n in notes:
                    print(f"  {n}")
                if confirm_continue("Delete these files?"):
                    for n in notes:
                        if n.is_file():
                            os.remove(n)
                else:
                    print("note files retained.")
            if Path(project.local_path).is_dir():
                if confirm_continue("Delete local project directory?"):
                    shutil.rmtree(project.local_path)
                else:
                    print("directory retained (deal with this ASAP)")
            project.sync_symlinks(remove=True)
            if confirm_continue(
                "Delete project manifest? This will completely remove the project from the registry, though local directories may exist on other systems."
            ):
                os.remove(Path(GLOBAL.paths["registry-dir"], name + ".json"))
        else:
            print("no matching project to delete.")

    def sync_aliases(self):
        alias_file_path = GLOBAL.paths["aliases_file"]
        lines = []

        # collect the top contents of the file which can be manually altered
        if alias_file_path.is_file():
            with open(alias_file_path, "r") as op:
                for i in op.readlines():
                    if i.startswith("# ~~ AUTO-GENERATED ALIASES BELOW ~~"):
                        break
                    else:
                        lines.append(i)

        # now create the list of auto-generated aliases from project directories
        # prepopulate the list with the main alias for this file
        aliases = [
            f"alias dubby='{Path(Path(__file__).parent.parent.resolve(), 'dubby.py')}'\n"
        ]
        for project in self.get_projects(local=True):
            workon_path = Path(project.local_path, ".workon")
            name = project.name.replace(" ", "-").replace("'", "")
            aliases.append(f"alias workon-{name}='source \"{workon_path}\"'\n")
            aliases.append(f"alias edit-workon-{name}='nano \"{workon_path}\"'\n")

        # ~~ AUTO-GENERATED ALIASES BELOW ~~
        with open(alias_file_path, "w") as op:
            op.writelines(lines)
            op.write("# ~~ AUTO-GENERATED ALIASES BELOW ~~\n")
            op.writelines(aliases)

        print("bash aliases updated. run:\n  source ~/.bashrc")

    def get_all_tags(self) -> list[str]:

        all_tags = set()
        for project in self.get_projects():
            for tag in project.tags:
                all_tags.add(tag)

        return sorted(list(all_tags))
