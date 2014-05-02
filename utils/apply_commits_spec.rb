#!/usr/bin/env ruby

RSpec.configure do |c|
  # declare an exclusion filter
  c.filter_run_excluding :broken => true
end

require './apply_commits.rb'

review_with_deps="91363"
review_is_dep="90075"
review_with_commit="90287/2"
review_in_library="90278"
review_in_main="90521" # Has more then 2 commits
review_with_many_commits="90391" # At least 8 commits
review_for_unknown_project="89508"
review_with_wrong_rev="90741/15"

describe 'helpers' do
  it 'get_rev should return revision info' do
    get_rev(review_with_many_commits)['revisions'].first[1]['_number'].should be >= 8
  end
  it 'show_rev_info should exist' do
    show_rev_info(get_rev(review_with_many_commits)).should include "#{review_with_many_commits}/"
    show_rev_info(get_rev(review_with_commit)).should include "#{review_with_commit}"
  end
  it 'make_args should work' do
    make_args("   #{review_with_deps}   #{review_is_dep}   ").should match Regexp.new("NAILGUN_GERRIT_COMMIT='refs/changes/\\d+/#{review_with_deps}/\\d+ refs/changes/\\d+/#{review_is_dep}/\\d+'")
    lambda{make_args(review_for_unknown_project)}.should raise_error
  end
  it 'make_args should aware dependencies', :broken => true do
    make_args(review_is_dep).should include review_is_dep
    lambda{make_args(review_with_deps)}.should raise_error
    make_args("#{review_with_deps} #{review_is_dep}").should match /#{review_is_dep}.*#{review_with_deps}/
  end
end
