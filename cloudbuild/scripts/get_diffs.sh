#!/bin/bash

set -e

bash_version=$(bash -version)
echo ""
echo "Running bash version: $bash_version"
echo ""

git rev-parse HEAD >>commit.txt
git rev-parse --short HEAD >>short_commit.txt

commit=$(cat commit.txt)

echo "############################"
echo "Working on commmit: $commit"
echo "Using base ref: ${BASE_BRANCH}"
if [[ ! -z "$PR_NUMBER" ]]; then
  echo "on pull request: #${PR_NUMBER}"
fi
echo "############################"

git config user.email "<>"
git config user.name "git"
git remote | xargs -n1 git remote remove
git remote add origin "${BASE_REPO_URL}"
echo "Remotes: "
git remote -vv

{
  git branch -D base-branch
} || {
  echo "continuing ... "
}
{
  git branch -D feature
} || {
  echo "continuing ..."
}

if [[ ! -z "$PR_N?UMBER" ]]; then
  git fetch origin "pull/${PR_NUMBER}/head":feature
  git fetch --unshallow
else
  git branch -m feature
fi

git fetch origin "${BASE_BRANCH}":base-branch
git checkout base-branch
git merge --no-ff feature

#!/bin/bash
build_diff_file="build-diff-file.txt"
diff=$(git diff --name-only origin/"${BASE_BRANCH}"...HEAD)
echo "Complete list of changed files:"
echo "$diff"

DIFF_IMAGES=""
DIFF_VERSION_FILE=""

for file in $diff; do
  if [[ "$file" =~ ^images/(.+)/VERSION$ ]]; then
    VERSION_FILE="${BASH_REMATCH[0]}"
    DIFF_IMAGES+="${BASH_REMATCH[1]}\n"
    version=$(cat $VERSION_FILE)
    if ! [[ "$version" =~ ^([0-9]|[1-9][0-9]+)\.?([0-9]|[1-9][0-9]+)\.?([0-9]|[1-9][0-9]+)$ ]]; then
      echo "ERROR: version file $VERSION_FILE does not contain a valid version number"
      exit 1
    fi
  fi
done

echo "Sorting and keeping unique changes ..."
echo ""
printf "$DIFF_IMAGES" | sort | uniq >DIFF_IMAGES.txt

if [[ -z "$DIFF_IMAGES" ]]; then
  echo "No images changed"
  exit 0
else
  echo "Images changed:"
  cat DIFF_IMAGES.txt
fi
