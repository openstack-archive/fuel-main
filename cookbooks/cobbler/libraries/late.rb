require "base64"

class LateFile
  def initialize(source, opts={})
    default_opts = {
      :method => :file
    }
    @source = source
    @opts = default_opts.merge(opts)
    @content = ""
    @content64 = base64(@content)
  end

  def init
    if @opts[:method] == :file
      open(@source , 'r') do |file| 
        lines = []
        while line = file.gets
          lines << line
        end
        @content = lines.to_s
      end
    elsif @opts[:method] == :content
      @content = @source
    end
    @content64 = base64(@content)
    return self
  end

  def content
    @content
  end

  def content64
    @content64
  end

  def base64(content)
    Base64.encode64(content).to_s.strip.gsub(/\n/, '')
  end

  def late_file(destfile, mode="644")
    "sh -c 'filename=${1}; shift; echo ${0} | base64 --decode > ${filename} && chmod #{mode} ${filename}' #{content64} #{destfile}"
  end

  def cobbler_late_file(destfile, mode="644")
    "sh -c 'filename=\\${1}; shift; echo \\${0} | base64 --decode > \\${filename} && chmod #{mode} \\${filename}' #{content64} #{destfile}"
  end
  

end







