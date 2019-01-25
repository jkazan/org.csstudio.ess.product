#!/bin/bash

VERSION=$1

declare -a repos=("https://github.com/jkazan/org.csstudio.display.builder.git"
                "https://github.com/jkazan/cs-studio-thirdparty.git"
                "https://github.com/jkazan/ess-css-extra.git"
                "https://github.com/jkazan/cs-studio.git"
                "https://github.com/jkazan/maven-osgi-bundles.git"
               )

for i in "${repos[@]}"
do
    git pull $i
    git commit -a -m "Merging $i with production version $VERSION"
done
