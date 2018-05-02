#!/usr/bin/env ruby
# encoding: utf-8
##################################################################################
# Google Scholar search scraper: lists main URLs given a phrase query and year   #
#                                                                                #
# Example: ./google-scholar-scraper.rb \                                         #
# "U.S. Government Work Not Protected by U.S. Copyright" 1975                    #
#                                                                                #
# CC-0, ArchiveTeam/WikiTeam, 2018                                               #
#                                                                                #
##################################################################################

require 'mechanize'
require 'uri'

urls = Array.new

a = Mechanize.new { |agent|
  agent.user_agent_alias = 'Linux Firefox' # e.g. with Konqueror the HTML is not ok for //h3/a search
}
prng = Random.new

search_result = a.get('https://scholar.google.it' )
search_form = search_result.forms.first
search_form.as_q = "%s" % ARGV[0]
search_form.as_ylo = ARGV[1]
search_form.as_yhi = ARGV[1]

search_result = a.submit(search_form, search_form.buttons.first)

# Continue clicking "Next" endlessly; exits at some point.
loop do
  search_result.search("//h3/a").each do |link|
    # The result URLs are in h3 headers and possibly passed through google.com/url?q=
    target = link['href']
    unless target.nil?
      # Take each result URI provided
      begin
        uri = URI.parse(target)
        # puts "Found URI: %s" % target
      rescue URI::InvalidURIError
        puts "Skipped invalid URI: %s" % target
        break
      end

      unless urls.include?(target)
      urls << target
      print '.'
      end

    end
  end

  sleep(prng.rand(10..60.0))
  begin
  # We click the "Next" link; replace with your language
  search_result = search_result.link_with(:text => 'Avanti').click
  rescue NoMethodError
    begin
    # Use the name of the link to repeat research with previously removed results. Doesn't work without leading space, in Italian!
    search_result = search_result.link_with(:text => ' ripetere la ricerca includendo i risultati omessi').click
    rescue NoMethodError
      break
    end
  rescue Net::HTTPServiceUnavailable
    puts "We got a 503, party is over"
    break
  end

  break if search_result.nil?

end

# Print all URLs found, one per line, to a file existing or new
output = File.open( "GS-PD-Gov.txt", "a")
urls.each do |url|
    output.puts url
end
output.close
