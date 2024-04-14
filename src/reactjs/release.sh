LOCAL_VERSION=$(cat package.json | grep -oh -m 1 "\d.\d.\d")
REMOTE_VERSION=$(npm view slth version)
echo "$REMOTE_VERSION >> $LOCAL_VERSION"
if [[ $LOCAL_VERSION != $REMOTE_VERSION ]]; then
  echo //registry.npmjs.org/:_authToken=$NPM_ACCESS_TOKEN > npmrc
  npm run build
  npm --userconfig npmrc publish
  rm npmrc
fi
