require "base64"

class LateFile
  def initialize(source_file)
    @source_file = source_file
    @content = ""
    @content64 = base64(@content)
  end

  def init
    open(@source_file , 'r') do |file| 
      lines = []
      while line = file.gets
        lines << line
      end
      @content = lines.to_s
      @content64 = base64(@content)
    end
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







