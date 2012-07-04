import xmlrpclib


server = xmlrpclib.Server('http://localhost/cobbler_api')
token = server.login('cobbler', '')


profile_id = server.get_profile_handle('profile0', token)
# server.modify_profile(profile_id, 'name', name, token)
# server.modify_profile(profile_id, 'distro', distro, token)
server.modify_profile(profile_id, 'kickstart', '/var/lib/mirror/preseed/precise.seed', token)
server.save_profile(profile_id, token)
