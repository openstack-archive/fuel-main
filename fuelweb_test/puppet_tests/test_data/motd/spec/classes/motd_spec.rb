require 'spec_helper'

describe 'motd' do
  it do
    should contain_file('/etc/motd').with({
      'ensure' => 'present',
      'owner'  => 'root',
      'group'  => 'root',
      'mode'   => '0644',
    })
  end

  it do
    should contain_file('/etc/motd').with_content('Hello!')
  end

end
