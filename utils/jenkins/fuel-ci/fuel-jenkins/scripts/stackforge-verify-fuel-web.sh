cd $WORKSPACE

#echo "the test is temporary unavailable and marked as failed"
#false
#exit 1
#false

cd $WORKSPACE/nailgun
npm install || true
cd $WORKSPACE

if [ -x ./run_tests.sh ]; then
  ./run_tests.sh --with-xunit
elif [ -x $WORKSPACE/nailgun/run_tests.sh ]; then
  cd $WORKSPACE/nailgun && ./run_tests.sh --with-xunit
else
  false
fi
