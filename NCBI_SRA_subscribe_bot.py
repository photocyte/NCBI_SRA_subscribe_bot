import sys
import requests
import argparse
import re
import xml
import xml.etree
import xml.etree.ElementTree as ET
import smtplib
import email.mime.text
import email.mime.multipart
import email.mime.text
import email.header
import xmljson
import json
import pandas
import datetime

now = datetime.datetime.now()
now_str = now.strftime("%Y-%m-%d %H:%M%p %Z")

pandas.set_option('display.max_colwidth', -1)

parser = argparse.ArgumentParser()
parser.add_argument('-t',required=True,type=int,metavar='NCBI_TAXONID')
parser.add_argument('-f',required=False,default=False,action='store_true')
parser.add_argument('--reldate',default=14,type=int)
parser.add_argument('--api_key',default=None,type=str)
parser.add_argument('--cachepath',default="/tmp/sra_bot",type=str)
parser.add_argument('--gmail_password',default=None,type=str)
parser.add_argument('--gmail_sender',default=None,type=str)
args = parser.parse_args()

sra_id_re = re.compile("Run acc=\"([0-9a-zA-Z_]+)\"")

def NCBI_lookup_taxon_name(taxonid,api_key=None):
    host="https://eutils.ncbi.nlm.nih.gov"
    search_url="/entrez/eutils/esearch.fcgi"
    terms = {'db':'taxonomy','term':str(taxonid)+'[uid]'}
    s = requests.post(host+search_url,data=terms)
    ids = []
    root = ET.fromstring(s.text)
    for child in root:
        if child.tag == "IdList":
            for subchild in child:
                ids.append(subchild.text)
    terms = {'db':'taxonomy','retmode':'xml','id':ids,'api_key':api_key}
    summary_url="/entrez/eutils/esummary.fcgi"
    summaries = requests.post(host+summary_url,data=terms)
    root_summary = ET.fromstring(summaries.text)
    for child in root_summary:
        for subchild in child:
            ##print(subchild.tag,subchild.attrib,subchild.text)  
            if 'Name' in subchild.attrib.keys() and subchild.attrib['Name'] == 'Rank':
                rank = subchild.text
            if 'Name' in subchild.attrib.keys() and subchild.attrib['Name'] == 'ScientificName':
                scientific_name = subchild.text
    if rank == None:
        rank = "no official rank"
    return rank,scientific_name

rank,name = NCBI_lookup_taxon_name(args.t)
sys.stderr.write("Looking up SRA records for "+rank+" "+name+" within the last "+str(args.reldate)+" days.\n")

host="https://eutils.ncbi.nlm.nih.gov"
search_url="/entrez/eutils/esearch.fcgi"
terms = {'db':'sra','term':'txid'+str(args.t)+'[Organism:exp]','retmax':50000000,'datetype':'pdat','reldate':args.reldate,'api_key':args.api_key}
s = requests.post(host+search_url,data=terms)

ids = set()
root = ET.fromstring(s.text)
for child in root:
    ##print(child.tag, child.attrib)
    if child.tag == "IdList":
        for subchild in child:
            ids.add(subchild.text)
id_list = ",".join(ids)
if len(id_list) == 0:
   sys.stderr.write("No records found.\n")
   exit()
else:
   sys.stderr.write(str(len(id_list))+" SRA database IDs returned from search.\n")

if not args.f:
    if len(id_list) > 10000:
        sys.stderr.write("More than 10,000 possible database records were returned. Not running out of a precaution. Use the '-f' switch to ignore this error and force the run.\n")
        exit()

terms = {'db':'sra','retmode':'xml','id':id_list,'retmax':50000000}
summary_url="/entrez/eutils/esummary.fcgi"
summaries = requests.post(host+summary_url,data=terms)

sys.stderr.write("Writing NCBI summary XML file to "+args.cachepath+".xml\n")
cache_file = open(args.cachepath+".xml","w")
cache_file.write(summaries.text)
cache_file.close()

html = '<!DOCTYPE html>\
<html lang="en">\
<head>\
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>\
</head>\
<body>'

html_footer = '</body>\
</html>'

text = "If you can't see the HTML table assosciated with this email, double check that your email client can read HTML."

##Could probably parse this all from ElementTree, but it broke my brain to think about XML so much.  Prefer the Python/Json syntax
##See here for the badgerfish standard: 
document_count = 0
root_summary = ET.fromstring(summaries.text)
documents = xmljson.badgerfish.data(root_summary)["eSummaryResult"]["DocSum"]

sys.stderr.write("Converting XML format to JSON/Python data structure\n")
##Iterate over individual SRA documents
for i in range(0,len(documents)):
    subdoc = documents[i]

    ##Convert Item to dict rather than list
    newDict = dict()
    for z in range(0,len(subdoc["Item"])):
        if "$" in subdoc["Item"][z].keys():
            newDict[subdoc["Item"][z]["@Name"]] = subdoc["Item"][z]["$"]
        else:
            newDict[subdoc["Item"][z]["@Name"]] = None

    subdoc["Item"] = newDict

    ##Parse internal XML into python data structures

    expXmlTxt = "<ExpXml>"+subdoc["Item"]["ExpXml"]+"</ExpXml>"
    expXmlData = xmljson.badgerfish.data(xml.etree.ElementTree.fromstring(expXmlTxt))
    runsTxt = "<Runs>"+subdoc["Item"]["Runs"]+"</Runs>"
    runsData = xmljson.badgerfish.data(xml.etree.ElementTree.fromstring(runsTxt))
    subdoc["Item"]["ExpXml"] = expXmlData
    subdoc["Item"]["Runs"] = runsData

sys.stderr.write("Writing NCBI SRA summary JSON file to "+args.cachepath+".json\n")
cache_file = open(args.cachepath+".json","w")
cache_file.write(json.dumps(documents,indent=4))
cache_file.close()

sys.stderr.write("NCBI SRA returned "+str(len(documents))+" documents.\n")

columns=["SRA_ID","Study","Title","Submitter","Species","Library type","# of reads","# of bp"]
SRA_DF = pandas.DataFrame(columns=columns)
for subdoc in documents:
   theData = dict()
   try:
       SRA_ID = subdoc["Item"]["Runs"]["Runs"]["Run"]["@acc"]
       theData["SRA_ID"] = "<a href=\"https://www.ncbi.nlm.nih.gov/sra/?term="+SRA_ID+"\">"+SRA_ID+"</a>"
       num_reads = subdoc["Item"]["Runs"]["Runs"]["Run"]["@total_spots"]
       theData["# of reads"] = 0
       if num_reads != "0" and num_reads != None:
           theData["# of reads"]=int(subdoc["Item"]["Runs"]["Runs"]["Run"]["@total_spots"])
   except TypeError:
       theData["SRA_ID"]="Multi_SRA"
       theData["# of reads"] = 0
       for r in subdoc["Item"]["Runs"]["Runs"]["Run"]:
           num_reads = r["@total_spots"]
           if num_reads != "0" and num_reads != None:
               theData["# of reads"] += num_reads

   theData["Study"]=subdoc["Item"]["ExpXml"]["ExpXml"]["Study"]["@name"]
   theData["Title"]=subdoc["Item"]["ExpXml"]["ExpXml"]["Summary"]["Title"]["$"]
   theData["Submitter"]=subdoc["Item"]["ExpXml"]["ExpXml"]["Submitter"]["@contact_name"]
   try:
       theData["Species"]=subdoc["Item"]["ExpXml"]["ExpXml"]["Organism"]["@ScientificName"]
   except KeyError:
       ##Try the common name
       theData["Species"]=subdoc["Item"]["ExpXml"]["ExpXml"]["Organism"]["@CommonName"]
   theData["Library type"]=subdoc["Item"]["ExpXml"]["ExpXml"]["Library_descriptor"]["LIBRARY_STRATEGY"]["$"]
   SRA_DF = SRA_DF.append(theData,sort=False,ignore_index=True)

SRA_DF = SRA_DF.sort_values(by=['Study', 'Title','Species','Library type','SRA_ID'])
SRA_DF = SRA_DF.reset_index(drop=True)
SRA_DF.index += 1

html += str(len(documents))+" SRA updates for "+rank+" "+name+" within the last "+str(args.reldate)+" days.<br>"
html += "This search ran on "+now_str+"<br>"
html += SRA_DF.to_html()
html = html.replace("&lt;","<")
html = html.replace("&gt;",">")
html += html_footer
##print(html)

sys.stderr.write("Writing NCBI SRA summary HTML table file to "+args.cachepath+".html\n")
cache_file = open(args.cachepath+".html","w")
cache_file.write(html)
cache_file.close()

if len(documents) > 0:
    sys.stderr.write("Now sending update email... ")
    pass
else:
    sys.stderr.write("No updates, so not sending email.")
    exit()

if args.gmail_password == None or args.gmail_sender == None:
    sys.stderr.write("\nERROR: Password or username not defined for email sending.\n")
    sys.stderr.write("Define these using the '--gmail_password' and '--gmail_sender' arguments")
    exit()

me = args.gmail_sender
you = args.gmail_sender
msg = email.mime.multipart.MIMEMultipart('alternative')
subject_str = str(len(documents))+" SRA updates for "+rank+" "+name+" within the last "+str(args.reldate)+" days."
subject = email.header.Header(subject_str, 'UTF-8')

msg['Subject'] = subject
msg['From'] = me
msg['To'] = you


part1 = email.mime.text.MIMEText(text, 'plain','utf-8')
part2 = email.mime.text.MIMEText(html, 'html','utf-8')
msg.attach(part1)
msg.attach(part2)

gmail_pwd=args.gmail_password

server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
server_ssl.ehlo() # optional, called by login()
server_ssl.login(me, gmail_pwd)  
server_ssl.sendmail(me, you, msg.as_string())
server_ssl.quit()
server_ssl.close()
sys.stderr.write('successfully sent the email.\n')

