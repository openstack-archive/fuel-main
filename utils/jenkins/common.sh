function license_check {
    # License information must be in every source file
    cd $WORKSPACE/local_repo
    tmpfile=`tempfile`
    find nailgun astute naily -regex ".*\.\(rb\|py\)" -type f -print0 | xargs -0 grep -L License > $tmpfile
    files_with_no_license=`wc -l $tmpfile | awk '{print $1}'`
    if [ $files_with_no_license -gt 0 ]; then
        echo "ERROR: Found files without license, see files below:"
        cat $tmpfile
        rm -f $tmpfile
        exit 1
    fi
    rm -f $tmpfile
}

function nailgun_checks {
    cd $WORKSPACE/local_repo/nailgun
    sudo service nailgun stop || :  # FIXME: let's remove fake UI completely from Jenkins master node

    # ***** Running Python unit tests, includes pep8 check of nailgun *****
    ./run_tests.sh --with-xunit  # --no-ui-tests

    # Cleaning database
    /usr/bin/psql -U postgres -c "drop database nailgun;"
    /usr/bin/psql -U postgres -c "create database nailgun owner nailgun;"

    # Loading data
    ./manage.py syncdb --noinput
    ./manage.py loaddefault
    ./manage.py loaddata nailgun/fixtures/sample_environment.json

    sudo service nailgun start || :
}

function ruby_checks {
    # Installing ruby dependencies
    echo 'source "http://rubygems.org"' > /tmp/product-gemfile
    cat requirements-gems.txt | while read gem ver; do \
            echo "gem \"$gem\", \"$ver\"" >> /tmp/product-gemfile; \
        done
    sudo bundle install --gemfile /tmp/product-gemfile

    cd $WORKSPACE/local_repo/astute
    rspec -c -fd spec/unit/
}
