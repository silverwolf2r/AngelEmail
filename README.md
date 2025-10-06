# AngelEmail
Automation of the Direct Send Email attack when given a website. This will crawl a website for emails and then from those emails attempt a direct send attack on the email server.

This is meant to be run from within Google CoLab and there are 2 blocks to it

###This will need to be the install block above everything else
%pip install requests beautifulsoup4 tldextract aiosmtpd
