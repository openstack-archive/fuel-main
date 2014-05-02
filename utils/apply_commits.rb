#!/usr/bin/env ruby

# Description
# -----------
# Convert reviews and revisions numbers to parameters for fuel make system
# Input example: apply_commits.rb 90391 91363 90287/2
# Output example:
#   # stackforge/fuel-web:master#90391/8 (Artem Roma) Checking of meta["interfaces"] section correctness
#   # stackforge/fuel-web:master#91363/1 (Artem Roma) Squashed migration added
#   # stackforge/fuel-library:master#90287/2 (Vladimir Sharshov) Set kernel params in grub config using web UI
#   export NAILGUN_GERRIT_COMMIT='refs/changes/91/90391/8 refs/changes/63/91363/1'
#   export FUELLIB_GERRIT_COMMIT='refs/changes/87/90287/2'
# Usage in shell script (pay attention to brackets):
#   COMMITS=`apply_commits 90391 91363 90287/2`
#   eval "$COMMITS"
# Additional options (turned on by default):
#   -v: show information about every patchset
#   -c: generate commands for cherry-picks in fuel-main (makesystem lack this ability)
# Dependency resolving (not implemented yet):
#   Child commit applied only after parent commit
#   Error is shown if parent commit is not in the list
# Gerrit api documentation: https://gerrit-review.googlesource.com/Documentation/rest-api.html

require 'optparse'
require 'ostruct'
require 'json'
require 'open-uri'

def make_args(revisions,verbose=false,cherrypick=false)
  project_to_key = {
    'stackforge/fuel-main' => "FUELMAIN_GERRIT_COMMIT",
    'stackforge/fuel-library' => "FUELLIB_GERRIT_COMMIT",
    'stackforge/fuel-web' => "NAILGUN_GERRIT_COMMIT",
    'stackforge/fuel-astute' => "ASTUTE_GERRIT_COMMIT",
    'stackforge/fuel-ostf' => "OSTF_GERRIT_COMMIT",
  }
  revs = revisions.split(" ").map{|rev| get_rev(rev)}
  refs = {}
  verb_out = []
  cherrypick_out = []
  revs.each do |rev|
    verbose and verb_out.push("    - #{show_rev_info(rev)}")
    refs[rev['project']].nil? and refs[rev['project']] = []
    refs[rev['project']].push(rev['revisions'].first[1]['fetch']['anonymous http']['ref'])
  end
  verb_out.empty? or verb_out = ["EXTRA_COMMITS=<<EOCOMMITS", "  extra_commits:"] + verb_out + ["EOCOMMITS"]
  if cherrypick and refs.has_key?("stackforge/fuel-main")
    cherrypick_out = refs['stackforge/fuel-main'].each.map { |ref|
      "git fetch https://review.openstack.org/stackforge/fuel-main #{ref} && git cherry-pick FETCH_HEAD"
    }
    refs.delete("stackforge/fuel-main")
  end
  params = refs.each.map { |prj, ref|
    project_to_key.has_key?(prj) or raise "Unknown project #{prj}"
    "export " + project_to_key[prj] + "='" + ref.join(" ") + "'"
  }
  (verb_out + params + [cherrypick_out.join(" && \\\n")]).join("\n")
end

def get_rev(revision)
  (review_id, rev_id) = revision.split("/")
  if rev_id.nil?
    uri = "https://review.openstack.org/changes/#{review_id}/detail"
    json = open(uri).read[5..-1]
    review = JSON.parse(json)
    rev_id = 0
    review['messages'].each do |msg|
      if msg['_revision_number'] > rev_id
        rev_id = msg['_revision_number']
      end
    end
  end
  uri = "https://review.openstack.org/changes/#{review_id}/revisions/#{rev_id}/review"
  json=open(uri).read[5..-1] # we need to remove extra chars at the beginning
  review = JSON.parse(json)
end

def show_rev_info(revision_data)
  project = revision_data['project']
  branch = revision_data['branch']
  review_id = revision_data['_number']
  rev_id = revision_data['revisions'].first[1]['_number']
  owner = revision_data['owner']['name']
  subject = revision_data['subject']
  "#{project}:#{branch}\##{review_id}/#{rev_id} (#{owner}) #{subject}"
end

if __FILE__ == $0
  options = OpenStruct.new
  options.verbose = true
  options.cherrypick = true

  OptionParser.new do |opts|
    opts.banner = 'Usage: etude5.rb [options]'
    opts.separator "\nOptions:"
    opts.on('-h', '--help', 'Show this message') do
      puts opts
      exit
    end
    opts.on('-v', '--[no-]verbose', 'Show detailed info about commits') do |flag|
      options.verbose = flag
    end
    opts.on('-c', '--[no-]cherry-pick', 'Provide commands for fuel-main cherry-picks') do |flag|
      options.cherrypick = flag
    end
    opts.on('-s', '--show REVISION', 'Show revision details') do |rev|
      puts show_rev_info(get_rev(rev))
      exit
    end
  end.parse!
  puts make_args(ARGV.join(" "), verbose=options.verbose, cherrypick=options.cherrypick)
end
