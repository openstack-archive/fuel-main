function license_check {
    # License information must be in every source file
    cd $WORKSPACE/local_repo
    tmpfile=`tempfile`
    find nailgun astute -not -path "astute/docs/*" -regex ".*\.\(rb\|py\|js\)" -type f -print0 | xargs -0 grep -Li License > $tmpfile
    files_with_no_license=`wc -l $tmpfile | awk '{print $1}'`
    if [ $files_with_no_license -gt 0 ]; then
        echo "ERROR: Found files without license, see files below:"
        cat $tmpfile
        rm -f $tmpfile
        exit 1
    fi
    rm -f $tmpfile
}

function nailgun_deps {
    # Installing nailgun dependencies
    if [ -n "${VIRTUAL_ENV}" ]; then
	pip install -r $WORKSPACE/requirements-eggs.txt
    else
	echo "INFO: install dependencies system-wide"
	sudo pip install -r $WORKSPACE/requirements-eggs.txt
    fi
}

function nailgun_checks {
    nailgun_deps
    cd $WORKSPACE/local_repo/nailgun

    # ***** Running Python unit tests, includes pep8 check of nailgun *****
    ./run_tests.sh --with-xunit # --no-ui-tests
}

function ruby_checks {
    cd $WORKSPACE/local_repo/astute
    WORKSPACE=$WORKSPACE/local_repo/astute ./run_tests.sh
}
