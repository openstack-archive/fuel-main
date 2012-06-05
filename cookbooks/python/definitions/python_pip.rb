# same as local_python_pip implementation

define :python_pip, :virtualenv => nil, :version => nil do
  local_python_pip params[:name] do
    virtualenv params[:virtualenv]
    version params[:version]
  end
end
