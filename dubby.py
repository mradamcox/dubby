#! /usr/bin/python3

import json
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
            "create",
            "delete",
            "add",
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
        "-m",
        "--message",
        help="message used for tagline or description input",
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

        project = registry.create_project(args.name, tags=args.tags)

    if o == "add":
        project = registry.get_project(args.name)
        if not project:
            print(
                "no project with this name exists! Use 'create' to make a new project from scratch."
            )
            exit()

        project.initialize_local()

    elif o == "delete":
        if confirm_continue(f"Deleting project {args.name}. Continue?"):
            registry.delete_project(args.name)

    elif o == "backup":
        project.backup(exclude=args.exclude)

    elif o == "list":
        check = "\u2713"
        table_rows = [["NAME", "LOCAL?", "TAGS", "TAGLINE"]]
        projects = registry.get_projects(
            tags=args.tags, status=args.status, local=args.local, org=args.org
        )
        for i in projects:
            table_rows.append(
                [
                    i.name,
                    check if i.is_local else "x",
                    ",".join(i.tags),
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
        project.set_description(args.message)

    elif o == "set-tagline":
        project.set_tagline(args.message)

    else:
        print("[ERROR] unsupported operation")
