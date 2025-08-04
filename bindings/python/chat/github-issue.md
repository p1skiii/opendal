Skip to content
Navigation Menu
PyO3
maturin

Type / to search
Code
Issues
87
Pull requests
11
Discussions
Actions
Security
Insights
Support for cargo workspaces #291
Closed
@g-braeunlich
Description
g-braeunlich
opened on Apr 6, 2020
In test-crates there is an example lib_with_path_dep referencing some_path_dep. However this example does not provide a pyproject.toml and also an own attempt to build such a project with pip install . fails for me.
My idea here would be to add support for cargo workspaces:
https://doc.rust-lang.org/book/ch14-03-cargo-workspaces.html
Basically this would mean: you have a top level project dir with a cargo.toml only specifying its members in the above example lib_with_path_dep and some_path_dep).
I would then put the section [package.metadata.maturin] into this file as [workspace.metadata.maturin] and also introduce a new field workspace.metadata.maturin.extension(s) specifying which of the members is a / the crate containing the pyO3 extension.
For mixed projects, the python code would now go to the toplevel directory together with (pyproject.toml / README.md).
What do you think?

Activity
konstin
konstin commented on Apr 18, 2020
konstin
on Apr 18, 2020
Member
FYI, the two crates in test-crates exist to test that is shown when using local (including workspace) dependencies as a test for #238. Also note that maturin develop and maturin build work fine, only source distributions are affected.

I think the most user friendly solution would be calling cargo package --list on each linked or transitively linked package in the workspace and adding them to the source distribution (This information is part of the cargo metadata output). If the root package is not directly in the workspace root than the location of the root package needs to be recorded somewhere, e.g. by adding a metadata key the workspace root Cargo.toml.


konstin
added 
enhancement
New feature or request
 on Apr 18, 2020
clbarnes
clbarnes commented on Apr 20, 2020
clbarnes
on Apr 20, 2020
Contributor
Somewhat related: my use case is a cargo workspace including a rust crate (for crates.io) and a pyo3-based wrapper using maturin, which is a mixed project and has a local dependency on the other crate. I'm trying to version them independently, but publishing with maturin produces an sdist which has a remote dependency on the published crate, and a wheel which packages the compiled result of the local dependency: potentially two different versions of the crate.

I think that either way (use the local, or use the published) would be fine (or could be worked around) so long as sdist and bdist were consistent.


ijl
mentioned this on Apr 27, 2020
sdist-include option #296
tari
tari commented on Jan 12, 2021
tari
on Jan 12, 2021
I recently had similar problems. I wanted to build a crate with multiple bindings in a workspace, something like:

Cargo.toml (workspace)
base/Cargo.toml (Rust core with external dependencies)
py/Cargo.toml (Python extension module, depends on base = { path = "../base" })
wasm/Cargo.toml (WASM bindings, depends on base)
While I was able to build wheels from in the py directory, maturin isn't able to build a sdist that works due to the path dependency. For now I've opted to use setuptools-rust instead since I can specify the path to the extension to build separately from the package root for sdist. (It also allows me to use different module and crate names, like #391.)

tafia
tafia commented on Feb 2, 2021
tafia
on Feb 2, 2021
Contributor
using maturin -m py/Cargo.toml seems to work for me.

konstin
konstin commented on Feb 24, 2021
konstin
on Feb 24, 2021
Member
Should be fixed by #441. Could you check whether v0.10.0-beta.1 works for you?


konstin
closed this as completedon Feb 24, 2021
tari
tari commented on Feb 24, 2021
tari
on Feb 24, 2021
It seems to be looking for lockfiles that don't necessarily exist here. With the same layout as #291 (comment) and lightly anonymized:

$ maturin --version
maturin 0.10.0-beta.1
$ maturin build -m py/Cargo.toml
🔗 Found pyo3 bindings
🐍 Found CPython 3.9 at python3.9
💥 maturin failed
  Caused by: Failed to build source distribution
  Caused by: Failed to add local dependency PACKAGE at .../base to the source distribution
  Caused by: Failed to add file from .../base/Cargo.lock to sdist as PACKAGE/local_dependencies/PACKAGE/Cargo.lock
  Caused by: No such file or directory (os error 2) when getting metadata for .../base/Cargo.lock
I have one Cargo.lock file next to the workspace's Cargo.toml, and created py/pyproject.toml so it will create an sdist. If no sdist is built, then things still seem to work (but of course there's no sdist).


konstin
mentioned this on Feb 26, 2021
Failure to package workspace with non-existinent lockilfes #449
MrNickArcher
MrNickArcher commented on Nov 7, 2022
MrNickArcher
on Nov 7, 2022
I tried and concluded that Maturin does not work with workspaces, I got it to build after messing with the configuration files for ages. But there are so many other small issues regarding package names vs crate names; the .pyd file doesnt get copied where it should; the mypackage.XXX.dist-info folder name does match the package folder in .env/Lib. Overall a bad time was had and I went back to the recommended package layout. A bit sad because it makes life hard if I want to concurrently develop python bindings alongside one or more reusable rust libraries.


robfitzgerald
mentioned this on Oct 28, 2023
pip install fails with "current package believes it's in a workspace when it's not" NREL/routee-compass#7

rabernat
mentioned this on Dec 16, 2023
Add pco_python to workspace pcodec/pcodec#141
dantliff-sqc
dantliff-sqc commented on Mar 25
dantliff-sqc
on Mar 25
For what it's worth, I was able to get maturin build to work for an individual crate in a cargo workspace by first changing to the directory of the crate's Cargo.toml, and run maturin from there. It seems to look back up the directory tree to find the workspace's root Cargo.toml without issue.

E.g.

$ cd py/my_pyo3_project/
$ maturin build
This also works for multiple PyO3 crates in the same workspace, just cd into the one you want to build.

I need to do this because I'm using Yocto to build my crates, and the python_maturin bbclass doesn't support -m syntax, so instead I set the source directory S variable to:

S = "${WORKDIR}/workspace/py/my_pyo3_project"
This is equivalent to running maturin from the my_pyo3_project directory itself.


rchen152
mentioned this on Jun 18
Cargo.lock uncommited facebook/pyrefly#432
p1skiii
Add a comment
new Comment
Markdown input: edit mode selected.
Write
Preview
Use Markdown to format your comment
Remember, contributions to this repository should follow its code of conduct.
Metadata
Assignees
No one assigned
Labels
enhancement
New feature or request
Type
No type
Projects
No projects
Milestone
No milestone
Relationships
None yet
Development
No branches or pull requests
NotificationsCustomize
You're not receiving notifications from this thread.

Participants
@tari
@konstin
@tafia
@clbarnes
@g-braeunlich
Issue actions
Footer
© 2025 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Docs
Contact
Manage cookies
Do not share my personal information
Support for cargo workspaces · Issue #291 · PyO3/maturin