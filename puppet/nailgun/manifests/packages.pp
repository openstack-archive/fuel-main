class nailgun::packages(
  $gem_source = "http://rubygems.org/",
  ){
  
  define nailgun_safe_package(){
    if ! defined(Package[$name]){
      @package { $name : }
    }
  }

  nailgun_safe_package { "supervisor": }
  nailgun_safe_package { "nginx": }
  nailgun_safe_package { "python-virtualenv": }
  nailgun_safe_package { "python-devel": }
  nailgun_safe_package { "gcc": }
  nailgun_safe_package { "make": }

}
