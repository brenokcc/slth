LOCAL_VERSION=$(cat setup.py | grep -oh -m 1 "\d.\d.\d")
REMOTE_VERSION=$(pip index versions pyslth | grep -oh -m 1 "\d.\d.\d")
echo "$REMOTE_VERSION >> $LOCAL_VERSION"
if [[ $LOCAL_VERSION != $REMOTE_VERSION ]]; then
  python setup.py sdist
  twine upload "dist/pyslth-$LOCAL_VERSION.tar.gz" -u __token__ -p $PIP_ACCESS_TOKEN
fi

