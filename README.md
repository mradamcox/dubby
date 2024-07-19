# dubby

A small project management application written in only with Python's standard library. The application integrates with a Dropbox folder to sync the project inventory across multiple hosts.

# Requirements

Python 3.8

# Setup

Clone this repo into your home directory like so (I like putting this in a hidden folder but you don't need to):

    git clone https://github.com/mradamcox/dubby ~/.dubby

Enter the reposdirectory and initialize it:

    cd ~/.dubby
    python3 ./dubby.py sync-aliases

Now in your `~/.bashrc` file add this to the end:

    if [ -f ~/.dubby/.bash_aliases ]; then
        . ~/.dubby/.bash_aliases
    fi

Run `source ~/.bashrc`.

Now you are ready to go! Run `dubby --help` to see the commands you can use.

TODO: the full setup workflow is not quite done, actually....

# Usage

`dubby create my_project`

1. Create a new project directory `my_project`, in the main projects directory
2. Create a `my_project/.workon` script inside with some boilerplate content
3. Will add a bash alias `workon-my_project` that will run the .workon script
4. Will add a bash alias `edit-workon-my_project` to open that script in nano
5. (and more)
