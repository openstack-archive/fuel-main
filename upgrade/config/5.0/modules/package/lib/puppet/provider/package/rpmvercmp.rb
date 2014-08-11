module Rpmvercmp

  def self.debug
    @debug = false unless defined? @debug
    @debug
  end

  def self.debug=(debug)
    @debug = debug
  end

  # check that the element is not fully integer
  def self.not_integer?(s)
    !Integer(s)
  rescue
    true
  end

  # convert label to epoch, version, release
  def self.label_to_elements(label)
    return [nil, nil, nil] unless label

    label = label.split ':'
    if label.length > 1
      epoch = label.shift
    else
      epoch = nil
    end
    label = label.join '-'

    label = label.split('-')
    if label.length > 1
      version = label.shift
      release = label.join '-'
    else
      version = label.first
      release = nil
    end

    [epoch, version, release]
  end

  def self.simple_checks(var1, var2)
    return 0 if var1 == var2
    return 1 if var1 and not var2
    return -1 if not var1 and var2
    0
  end

  # compare two blocks
  # first is larger -> 1
  # second is larger -> -1
  # equal -> 0
  def self.compare_blocks(block1, block2)
    block1 = get_string block1
    block2 = get_string block2
    rc = simple_checks block1, block2
    return rc if rc != 0

    # ~ sign has the highest sorting priority
    if block1.start_with? '~' and !block2.start_with? '~'
      return 1
    elsif !block1.start_with? '~' and block2.start_with? '~'
      return -1
    end

    if not_integer?(block1) && not_integer?(block2)
      # Both not integers:
      # compare strings
      block1 <=> block2
    else
      # One of elements is integer:
      # convert both to int and compare
      block1.to_i <=> block2.to_i
    end
  end

  # compare two elements
  # first is larger -> 1
  # second is larger -> -1
  # equal -> 0
  def self.compare_elements(element1, element2)
    element1 = get_string element1
    element2 = get_string element2
    rc = simple_checks element1, element2
    return rc if rc != 0

    # split both versions to elements
    separators = /[\._\-+]/
    blocks1 = element1.split separators
    blocks2 = element2.split separators

    # compare each element from first to same element from second
    while blocks1.length > 0 or blocks2.length > 0
      b1 = blocks1.shift
      b2 = blocks2.shift
      rc = compare_blocks b1, b2
      puts "Blocks: #{b1} vs #{b2} = #{rc}" if debug
      # return result on first non-equal match
      return rc if rc != 0
    end
    # there is nothing left to compare: return equal
    0
  end

  def self.get_string(value)
    return '' unless value
    value.to_s
  end

  def self.compare_fuel(label1, label2)
    return 0  if label1 == label2
    return 0  if !label1.include? 'fuel' and !label2.include? 'fuel'
    return 1  if label1.include?  'fuel' and !label2.include? 'fuel'
    return -1 if !label1.include? 'fuel' and label2.include?  'fuel'

    label1 =~ /fuel([\d\.]*)/
    ver1 = $1
    label2 =~ /fuel([\d\.]*)/
    ver2 = $1
    compare_elements ver1, ver2
  end

  def self.compare_labels(label1, label2)
    label1 = get_string label1
    label2 = get_string label2
    rc = simple_checks label1, label2
    return rc if rc != 0

    rc = compare_fuel label1, label2
    puts "Fuel: #{rc}" if debug
    return rc if rc != 0

    elements1 = label_to_elements label1
    elements2 = label_to_elements label2

    while elements1.length > 0 or elements2.length > 0
      e1 = elements1.shift
      e2 = elements2.shift
      rc = compare_elements e1, e2
      puts "Elements: #{e1.inspect} vs #{e2.inspect} = #{rc}" if debug
      return rc if rc != 0
    end
    0
  end

end
