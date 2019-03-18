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

msg="Merge master into production."

declare -a gitcmds=(
    "git checkout production"
    "git pull origin production"
    "git merge master -m \"Merge master into production.\""
    "git push origin production"
    "git tag ESS-CS-Studio-$VERSION"
    "git checkout master"
)

git commit -a -m "Updating changelog, splash, manifests to version $VERSION"
git push origin

for i in "${repos[@]}"; do
    cd ../$i/
    for k in "${gitcmds[@]}"; do
        echo -e "\nRunning: $k"
        $k
        # if [ "$k" = "asdasd" ]; then
        #     git merge master -m "Merge master into production."
        #     echo -e "\nRunning: git merge master -m \"Merge master into production.\""
        # else
        #     echo -e "\nRunning: $k"
        #     $k
        # fi
        ret_code=$?
        echo "return code: ${ret_code}"
        if [[ ${ret_code} != 0 ]]; then
            echo "ERROR occurred running: $k"
            exit 1
        fi
    done
done
