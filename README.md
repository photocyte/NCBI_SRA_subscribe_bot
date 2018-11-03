# NCBI_SRA_subscribe_bot
This is a python bot that emails you when new sequencing data from particular taxa is available on SRA.

##Dependencies

 * python3
 * xmljson
 * pandas

 
##Usage 

`python3 NCBI_SRA_subscribe_bot.py -t 94777 --reldate 360 --gmail_password YOURPASSWORDHERE --gmail_sender YOUR_GOOGLE_EMAIL_ADDRESS`

This would report all the elaterid (Family Elateridae) sequences which have released in the past year.

Scheduling isn't handled by this script. The the idea is you'd use a scheduler for your own OS.  E.g. cron

##FAQ
 * Q: I have to put my password into the command line, is my email password exposed?
 * A: Not over the internet, as it is protected by SSL encryption to Google's SMTP server, but it is good practice to ensure only your user account can read the file which has your password in plaintext. (e.g. the crontab)
