#! /usr/bin/python3

import json
import shutil
import argparse

from app.models import Registry
from app.utils import confirm_continue, print_table

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "operation",
        choices=[
            "list",
            "info",
            "sync-aliases",
            "sync-symlinks",
            "sync-notes",
            "create",
            "add",
            "remove",
            "backup",
            "set-active",
            "set-inactive",
            "set-archived",
            "set-description",
            "set-tagline",
            "add-tags",
            "remove-tags",
            "list-orgs",
            "list-tags",
        ],
    )
    parser.add_argument(
        "name",
        nargs="?",
        help="project name",
    )
    parser.add_argument(
        "-t",
        "--tags",
        nargs="*",
        default=[],
        help="one or more tags",
    )
    parser.add_argument(
        "-d",
        "--description",
        help="description of project, used during create --no-input or set-description",
    )
    parser.add_argument(
        "--tagline",
        help="tagline for project, used during create --no-input or set-tagline",
    )
    parser.add_argument(
        "-s",
        "--status",
    )
    parser.add_argument(
        "-o",
        "--org",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--no-tagline",
        action="store_true",
        default=False,
        help="when listing projects, only those without taglines",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="directory or file names to exclude during backup",
    )
    parser.add_argument(
        "--no-input",
        action="store_true",
        help="use cli arguments to create a project, don't use interactive input",
    )
    parser.add_argument(
        "--target",
        help="path to external Projects directory to send archive to"
    )
    args = parser.parse_args()

    registry = Registry()

    o = args.operation

    print(f"operation: {o}")
    if args.name:
        print(f"project: {args.name}")

    print(25 * "-")

    ## because most operations are undertaken on a project, just find it now and use
    ## it later.
    project = None
    if args.name and o != "create":
        project = registry.get_project(args.name)
        if project is None:
            print("No project found by that name.")
            exit()

    if o == "create":
        project = registry.get_project(args.name)
        if project:
            print("project with this name already exists!")
            print(project.serialize())
            exit()

        if args.no_input:
            project = registry.create_project(
                args.name,
                description=args.description,
                tags=args.tags,
                tagline=args.tagline,
            )
        else:            
            tagline = None
            while not tagline:
                tagline = input("tagline (required): ")
            
            description = input("description (optional): ")
            if not description:
                description = None

            print("existing tags on other projects:")
            print(registry.get_all_tags())
            input_tags = input("tags for this project (multiple ok, separate with commas): ")
            clean_tags = [i.lstrip().rstrip() for i in input_tags.split(",")]

            props = {
                "tags": clean_tags,
                "tagline": tagline,
                "description": description,
            }

            print("SUMMARY:")
            print(f"new project: {args.name}")
            org = None
            if "__" in args.name:
                org = args.name.split("__")[0]
            if org:
                print(f"  -- org: {org}")
            else:
                print("  (no organization)")
            print(json.dumps(props, indent=1))

            input("\nlooks good? hit enter to continue, or ctrl+c to abort")

            project = registry.create_project(args.name, **props)

    elif o == "add":
        project = registry.get_project(args.name)
        if not project:
            print(
                "no project with this name exists! Use 'create' to make a new project from scratch."
            )
            exit()

        project.initialize_local()
        project.sync_symlinks()
        registry.sync_aliases()

    elif o == "remove":
        if confirm_continue(f"Beginning removal of {args.name}. Continue?"):
            registry.delete_project(args.name)

    elif o == "backup":
        if not project.is_local:
            print("This project does not exist locally and can't be backed up.")
            exit()
        archive_path = project.backup(target=args.target, exclude=args.exclude)
        print(f"archive created: {archive_path}")

        if confirm_continue("Do you also want to remove the local project directory?", default=False):
            print(f"deleting directory: {project.local_path}")
            shutil.rmtree(project.local_path)
            if confirm_continue("Set status to archived?", default=False):
                project.set_status("archived")

    elif o == "list":
        check = "\u2713"
        table_rows = [["NAME", "LOCAL?", "TAGLINE"]]
        projects = registry.get_projects(
            tags=args.tags, status=args.status, local=args.local, org=args.org
        )
        if args.no_tagline:
            projects = [i for i in projects if not i.tagline]
        for i in projects:
            table_rows.append(
                [
                    i.name,
                    check if i.is_local else "x",
                    i.tagline if i.tagline else "",
                ]
            )

        print_table(table_rows)
        print(f"---\ncount: {len(projects)}")

    elif o == "list-orgs":
        projects = registry.get_projects(
            tags=args.tags, status=args.status, local=args.local, org=args.org
        )
        orgs = sorted(set([i.org for i in projects if i.org]))
        for org in orgs:
            print(org)
        print(f"---\ncount: {len(orgs)}")

    elif o == "list-tags":
        projects = registry.get_projects(
            tags=args.tags, status=args.status, local=args.local, org=args.org
        )
        tags = set()
        for p in projects:
            tags = tags | set(p.tags)
        tags = sorted(tags)
        for tag in tags:
            print(tag)
        print(f"---\ncount: {len(tags)}")

    elif o == "info":
        print(json.dumps(project.serialize(), indent=2))

    elif o == "sync-aliases":
        registry.sync_aliases()

    elif o == "sync-symlinks":
        if project:
            if project.is_local:
                project.sync_symlinks()
            else:
                print("[WARNING] This project doesn't exist locally.")
        else:
            for p in registry.get_projects(org=args.org, local=True):
                print(p.name)
                p.sync_symlinks()

    elif o == "sync-notes":
        if project:
            if project.is_local:
                project.sync_logseq_notes()
            else:
                print("[WARNING] This project doesn't exist locally.")
        else:
            for p in registry.get_projects(org=args.org, local=True):
                print(p.name)
                p.sync_logseq_notes()

    elif o == "set-active":
        project.set_status("active")

    elif o == "set-inactive":
        project.set_status("inactive")

    elif o == "set-archived":
        project.set_status("archived")

    elif o == "add-tags":
        project.add_tags(args.tags)
        print(f"tags: {project.tags}")

    elif o == "remove-tags":
        project.remove_tags(args.tags)
        print(f"tags: {project.tags}")

    elif o == "set-description":
        project.set_description(args.description)

    elif o == "set-tagline":
        project.set_tagline(args.tagline)

    else:
        print("[ERROR] unsupported operation")
