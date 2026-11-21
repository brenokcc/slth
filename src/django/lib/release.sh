source ../../../.venv/bin/activate
pip install --upgrade pip
LOCAL_VERSION=$(cat setup.py | grep -oh -m 1 "\d.\d.\d")
REMOTE_VERSION=$(pip index versions slthlib 2>/dev/null | grep -Eo -m 1 "[0-9]+\.[0-9]+\.[0-9]+")
echo "$REMOTE_VERSION >> $LOCAL_VERSION"
if [[ $LOCAL_VERSION != $REMOTE_VERSION ]]; then
  python setup.py sdist
  twine upload "dist/slthlib-$LOCAL_VERSION.tar.gz" -u __token__ -p $PIP_ACCESS_TOKEN
fi