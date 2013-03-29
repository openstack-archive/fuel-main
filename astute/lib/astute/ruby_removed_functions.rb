class Date
  def self.day_fraction_to_time(fr)
    ss,  fr = fr.divmod(Rational(1, 86400))
    h,   ss = ss.divmod(3600)
    min, s  = ss.divmod(60)
    return h, min, s, fr
  end
end