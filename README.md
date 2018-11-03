# NCBI_SRA_subscribe_bot
This is a python script/bot which is intended to run on a regular basis (e.g. every week, or every 2 weeks), and email you when new SRA records from a particular taxonomic grouping are available.  

SRA *may* have an capability to allow you to subscribe to new data, but if it exists I haven't found it.


## Dependencies

 * python3
 * xmljson
 * pandas

 
## Usage 

`python3 NCBI_SRA_subscribe_bot.py -t 94777 --reldate 360 --gmail_password YOURPASSWORDHERE --gmail_sender YOUR_GOOGLE_EMAIL_ADDRESS`

This would report all the elaterid (Family Elateridae) sequences which have released in the past year.

`python3 NCBI_SRA_subscribe_bot.py -h` to see the help documentation

Scheduling isn't handled by this script. The the idea is you'd use a scheduler for your own OS.  E.g. cron to run the script every 2 weeks, and then 

## FAQ
 * Q: I have to put my password into the command line to enable automatically emailing of results, is my email password exposed?
 * A: Yes and no.  Your password isn't exposed when going over the internet, as it is protected by SSL encryption to Google's SMTP server, but your password is in plaintext on the script, so if another user can read that file (e.g. the crontab), the password would be exposed.
 * Q: Can other email services than GMail be used?
 * A: Yes, but would require support to be written into the script. 
