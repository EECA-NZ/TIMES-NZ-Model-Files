# Editing documentation (for non-developers)

This page is written for researchers and experts who wish to edit or comment on the documentation, but they have no experience with git or coding. The process is very straightforward, but might be unfamiliar for some. 

```{eval-rst}
.. admonition:: Alternative: working with Word files
   :class: note

   If preferable, it's possible to instead edit/comment on the Word files generated from the documentation code.
   
   Note that single source of truth is **always** stored as code on git. If you edit or comment in Word, a developer will need to incorporate your changes to the codebase themselves. 
```


## Required software

The necessary software is available on EECA's Company Portal for internal researchers. It's also just available free for anyone. 

Please install: 

 - [git](https://git-scm.com/) 
 - (optional, but highly recommended) a decent plaintext editor. [VSCode](https://code.visualstudio.com/download) is very popular. 
 - (optional - if you want to test local changes) - [python](https://www.python.org/downloads/)

You will also need to make a [github](https://github.com/) account if you don't already have one. 

## Setup using the terminal

1): Open "Windows Powershell" from your start menu, and a terminal window will open.  

```{eval-rst}
.. admonition:: Working directories
   :class: note   

   Terminal commands will always be executed in the current "working directory". Right now, that is your user directory. You can tell by the address listed in the terminal, which should read:

   `PS C:\\Users\\[your_user_name]>`
```

2): Choose a name for your working folder. In this example, we'll call it "repos", but it can be anything you like. 

3): Type: `mkdir repos`, then press enter. This uses `mkdir` ("make directory") to create a new folder, called "repos".

4): Type `cd repos`, and press enter. This uses `cd` ("Change directory") to move the terminal's working directory to the "repos" folder you created. 

5): Use git to "clone the repo", or make a local copy of the codebase. In the terminal, enter

```
git clone -b dev https://github.com/EECA-NZ/TIMES-NZ-Model-Files.git
```

This uses git's `clone` command to fetch the development (`dev`) version of the source code from our remote repository. It takes a little minute to download everything. 

You now have a copy of the entire project on your computer. You can check that same folder in Windows Explorer to see everything, or `cd` into the project folder and then enter `ls` to see all the files and folders.

## Editing the documents 

Every time you want to edit the files, it's best practise to make a separate git branch to work on. This keeps your changes separate from everyone else's, and it's easy for us to see who changed what. 

First, ensure your terminal is in the `TIMES-NZ-Model-Files` directory you've created, then make a new branch with the powershell command: 

```
git checkout -b your_branch_name
```

Now, you can make whatever changes you like. The source documents are all in `PREPARE-TIMES-NZ/docs/source`. More fulsome documentation on working with the documentation files is available [here](documentation_maintenance.md). 

When you have finished making changes, enter the following git commands: 

 - Use `git status` to see the name of your current branch, and any changed files. Files will be red if unstaged, but green if ready to go. 
 - Use `git add .` to add all your changes to the staging area, or `git add filename` to add just specific files 
 - Use `git commit -m "add some message here"` to commit (save) all your staged changes. 
 - Use `git push` to send your committed changes to the repo. Note that this won't work the first time, but git will generate the correct command for you to set the upstream branch. 
 - Visit your branch on the [repo](https://github.com/EECA-NZ/TIMES-NZ-Model-Files) (you should be able to see it in the branch dropdown) and use the github UI to make a Pull Request. This will create a template where you can describe your changes and request a review. 























