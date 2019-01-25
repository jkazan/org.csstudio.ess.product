import os
import sys
import requests
import re
import subprocess
import fileinput
from getpass import getpass
import platform

def checkVersion(user_input):
    """Checks the CSS version input against artifactory.

    Grabs latest CSS version number from
    https://artifactory.esss.lu.se/artifactory/CS-Studio/production/ and
    increments nano version (i.e. last number) by one. If the resulting
    number differs from user input, the user is prompted for
    verification to continue anyway.

    Args:
        user_input: Version number as string, input by user.
    """
    url = "https://artifactory.esss.lu.se/artifactory/CS-Studio/production/"
    pattern = re.compile("[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+") # version pattern
    params = {"q": "ISOW7841FDWER"}
    headers = {"User-Agent": "Mozilla/5"}
    r = requests.get(url, params=params, headers=headers)

    versions = set(pattern.findall(r.text)) # A set containing all versions
    latest = ""
    latest_sum = 0

    # Find latest version
    for v in versions:
        split = v.split(".")
        factor = 1
        version_sum = 0
        for n in reversed(split):
            version_sum += int(n)*factor
            factor*=100
        if version_sum > latest_sum:
            latest_sum = version_sum
            latest = v

    # New version suggestion is latest version + 1 (increment nano version)
    new_version = ".".join([
        ".".join(latest.split(".")[:-1]),
        str(int(latest.split(".")[-1])+1)
        ])

    # If user input version is not same as next nano version, prompt user
    if new_version != user_input:
        print("Suggested version number is {}" .format(new_version))
        accepted = {"yes": True, "y": True, "no": False, "n": False}
        while True:
            choice = input("Are you sure you wish to use {}? [y/n]"
                                   . format(user_input)).lower()
            if choice not in accepted:
                print("\x1b[31mPlease answer with 'y' or 'n'.\x1b[0m")
            elif not accepted[choice]:
                print("Aborting")
                sys.exit()
            else:
                return

# def checkJavaHome():
#     java_home = subprocess.check_output("echo $JAVA_HOME", shell=True).decode("utf8")
#     print(java_home)
#     if java_home.isspace():
#         print("You don't seem to have a path in the JAVA_HOME variable")
    #     if platform.system() == "Linux":
    #         suggestion_cmd = "dirname $(readlink -f $(which java))"
    #     elif platform.system() == "Darwin":
    #         suggestion_cmd = "dirname $(readlink $(which java))"

    #     suggestion = subprocess.check_output(suggestion_cmd, shell=True).decode("utf8")
    #     print("Put the following your `.bashrc` file or `.profile` file:\n{}"
    #               .format(suggestion))

def prepareRelease(path, release_url, version, notes, ce_version):
    """Run `prepare-release.sh`.

    `prepare-release.sh` is a community developed script for creating
    new splash screen, change 'about' dialog, change Ansible reference
    file, update plugin versions, update product versions in product
    files, update product versions in master POM file and
    commit-tag-push changes.

    Args:
        path: Path to `prepare-release.sh`.
        release_url: Url to Jira release page.
        version: CSS release version to prepare.
        notes: Notes to be inserted into the changelog.
        ce_version: CSS CE version of which the CSS release is based on.
    """
    prepare_release_cmd = str(
        'bash {}prepare-release.sh {} "{}" "{}</li><li>' \
        'Based on CS-Studio CE {}-SNAPSHOT" true'
    .format(path, version, release_url, notes, ce_version))

    subprocess.check_call(prepare_release_cmd, shell=True)

def prepareNextRelease(version): #TODO: Test function
    """Run `prepare-next-release.sh`.

    `prepare-next-release.sh` is a community developed script for
    preparing splash screen, change 'about' dialog, change Ansible
    reference file, updating plugin versions, update product versions in
    master POM file, commit version and push changes.

    Args:
        version: CSS version of current release, i.e. not next version.
    """
    # Determine next version by incrementing nano version of the current release
    next_version = ".".join([
        ".".join(version.split(".")[:-1]),
        str(int(version.split(".")[-1])+1)
        ])

    path = os.path.dirname(os.path.abspath(__file__))+"/"

    prepare_next_release_cmd = str("bash {} prepare-next-release.sh {} false"
                                       .format(path, next_version))

    subprocess.check_call(prepare_next_release_cmd, shell=True)

def replace(path, pattern, repl):
    """Replace a pattern in a file.

    Inplace relpacement of text in a file. Original file will be backed
    up with <filename>.bak

    Args:
        path: Path to file in which to replace text.
        pattern: Regular expression pattern to search fore.
        repl: Replacement text with which to replace text matching to `pattern`.
    """
    pat = re.compile(pattern)
    with fileinput.FileInput(path, inplace=True, backup=".bak") as file:
        for line in file:
            result = re.sub(pat, repl, line)
            print(result, end="")

def updatePom(path, version):
    """Update pom.xml file.

    Update cs-studio major, and minor, version number in pom.xml file.

    Args:
        path: Path to pom.xml file
        version: Full CSS version number to be released, e.g. 4.6.1.12
    """
    split = version.split(".")
    majmin = ".".join(split[0:2])
    pattern = "<cs-studio.version>[0-9]+\.[0-9]+</cs-studio.version>"
    replacement = "<cs-studio.version>" + majmin + "</cs-studio.version>"
    replace(path, pattern, replacement)

def getChangelogNotes(version):
    """Get notes for changelog from Jira.

    Get notes from Jira via REST interface and format the notes to be
    accepted by the `prepare-release.sh` script (see function
    `prepareRelease` in this file for more info.).

    Args:
        version: Full CSS version number to be released, e.g. 4.6.1.12
    """

    # Jira login information
    # user = input("Username: ")
    # passw = getpass("Password: ")
    user = "johanneskazantzidis"
    passw = "Saraeva1"
    auth = (user, passw)
    headers = {"Content-Type":"application/json"}

    # REST url for issues specific for the release
    url = 'https://jira.esss.lu.se/rest/api/2/' \
      'search?jql=project=CSSTUDIO AND fixVersion="ESS CS-Studio '+version+'"'
      #TODO: error handling / empty return handling

    response = requests.get(url, auth=auth, headers=headers)
    data = response.json()
    note_list = []
    pattern = re.compile("CSS-CE #[0-9]+")

    # `CSS-CE #XXX` is a merge from the community version. Sort `note_list`
    # with CSS-CE merges first.
    for issue in data["issues"]:
        summary = issue["fields"]["summary"]
        if list(pattern.findall(summary)):
            note_list.insert(0,"<li>"+summary+"</li>")
        else:
            note_list.append("<li>"+summary+"</li>")

    # Now that the comment_list is sorted, put them into one string to fit the
    # format expected by the prepare-realease.sh script
    notes_str = ""
    for note in note_list:
        notes_str += note

    # The `prepare-release.sh` script will put <li></li> around the note
    # string. Since several notes may be used, <li></li> must be added around
    # each note as above. To satisfy the `prepare-release.sh` script however,
    # the first <li> and the last </li> of `notes_str` must be excluded. One
    # may be tempted to modify the `prepare-release.sh` script instead, though
    # as it is made by, and spread amongst, the community it is decided to be
    # kept intact for the time being.
    formatted_notes = notes_str[4:-5]

    return formatted_notes

def mergeRepos(path, version):
    """Merge all relevant repositories into production.

    Args:
        path: Path to `merge.sh`.
        version: CSS version for this release.
    """
    merge_cmd = str("bash {} {}" .format(path, version))

    subprocess.check_call(merge_cmd, shell=True)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CSS release tool")
    parser.add_argument("version", type=str, help="New release version")
    parser.add_argument("ce_version", type=str, help="CS-Studio CE versopm " \
                            "that new release is based on")

    args = parser.parse_args()

    checkVersion(args.version)
    # checkJavaHome() #TODO: perhaps make this function
    release_url = "https://jira.esss.lu.se/projects/CSSTUDIO/versions/23001"
    dir_path = os.path.dirname(os.path.abspath(__file__))+"/"

    notes = getChangelogNotes(args.version)
    prepareRelease(dir_path, release_url, args.version, notes, args.ce_version)
    updatePom(dir_path+"pom.xml", args.version)
    mergeRepos(dir_path+"merge.sh", args.version)
    # # Commit org.csstudio.ess.product to master branch
    # # Do pull request
    # # Merge the master branch of the corresponding ESSICS repository into the production one, and tag it.
    # # TALK TO CLAUDIO BEFORE THIS STEP: Start the production pipeline in Jenkins.
    # prepareNextRelease(args.version)
    # # Commit everything to master branch.
    # # Update the ESS CS-Studio Releases page.
    # # Create a new TechNew.

    # # Be sure the CS-Studio User's Manual document was updated to document all the new/updated features to be released.
    # # Update the CS-Studio Compatibility Notes and Known Bugs document (last version comes first).
    # # From the CS-Studio Kanban board on Atlassian, release the new version, pressing the Release… link (see Figures 6 and 7).
