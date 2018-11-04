# NCBI_SRA_subscribe_bot
This is a python script/bot which is intended to run on a regular basis (e.g. every week, or every 2 weeks), and email you when new [NCBI SRA](https://www.ncbi.nlm.nih.gov/sra) records from a particular taxonomic grouping are available.  

The SRA *may* already allow you to subscribe to new data by email updates in this way, but if it exists I haven't found it. (Please let me know if you are aware of such a service!)

The script uses realtime querying of the NCBI databases, and uses Gmail's SMTP server to send the email, so internet access to those servers is required.


## Dependencies

 * python3
 * xmljson
 * pandas

 The rest of the dependencies should be included with standard python3 installs.

 
## Usage 

`python3 NCBI_SRA_subscribe_bot.py -t 94777 --reldate 360 --gmail_password YOURPASSWORDHERE --gmail_sender YOUR_GOOGLE_EMAIL_ADDRESS`

This script command line would email you all the elaterid (Family Elateridae; NCBI taxon id 94777) sequences which have released in the past year.

`python3 NCBI_SRA_subscribe_bot.py -h` to see the help documentation

The scheduling to run regularly isn't handled by this script. The idea is you'd use a scheduler for your own OS to regularly run the script without your supervision.  E.g. cron to run the script every 2 weeks 

## FAQ
 * Q: I have to put my password into the command line to enable automatically emailing of results, is my email password exposed?
 * A: Yes and no.  Your password isn't exposed when going over the internet, as it is protected by SSL encryption to Google's SMTP server, but your password is in plaintext on the script, so if another user can read that file (e.g. the crontab file), the password would be exposed.

 * Q: Can other email services than GMail be used?
 * A: Yes, but would require support to be written into the script. It's not so hard, as it would be handled by smtplib.
