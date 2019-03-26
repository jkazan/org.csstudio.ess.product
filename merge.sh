#!/bin/bash

VERSION=$1

declare -a repos=(
    "ess-css-extra"
    "maven-osgi-bundles"
    "cs-studio-thirdparty"
    "cs-studio"
    "org.csstudio.display.builder"
    "org.csstudio.ess.product"
)

declare -a gitcmds=(
    "git checkout test"
    "git pull"
    "git checkout production"
    "git pull"
    "git merge test -m 'test message'"
    # "git fetch origin"
    # "git checkout test"
    # "git checkout production"
    # "git pull origin production"
    # "git merge test -m 'test message'"
    "git push origin production"
    "git tag ESS-CS-Studio-$VERSION"
    "git checkout test"
)

git commit -a -m "Updating changelog, splash, manifests to version $VERSION"
git push origin

for i in "${repos[@]}"; do
    cd ../$i/
    for k in "${gitcmds[@]}"; do
        $k
        if [[ $? != 0 ]]; then
            echo "Error occurred running: $k"
            exit 1
        fi
    done
done




# TODO: CHANGE TEST TO MASTER!
