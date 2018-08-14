#!/bin/python

import sys
import subprocess
import time
import logging
import os
import smtplib
import daemon
from configparser import ConfigParser
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

#Read configuration
cfg = ConfigParser()
cfg.read('config.ini')
run_as_daemon = cfg.getboolean('daemonization','run_as_daemon')
log_path = cfg.get('logging','logPath')
freq = float(cfg.get('watchdog','time'))
retry = float(cfg.get('watchdog','retry'))
probing = float(cfg.get('watchdog','probing'))
service = cfg.get('watchdog','service')
mail_user = cfg.get('notification','mail_user')
mail_password = cfg.get('notification','mail_password')
to = cfg.get('notification','to')
subject = cfg.get('notification','subject')
body = cfg.get('notification','body')
host = os.uname()[1]

#write_log writes to a defined log
def write_log(severity, message):
    f=open(log_path, "a+")
    f.write(time.ctime() + " " + severity + ": " + message + "\n")
    f.close() 

#watchdog function restarts service if it is down. 
#Logs numer of attempts and results, sends email whether service have been or could not be started and attempts
def watchdog(service, retry, freq):
    if not (is_running(service)):
        i = 0
        while i < retry:
            i = i + 1
            write_log("INFO", 'Attempt nr %d to start %s.' % (i,service))
            start_service(service)
            if (is_running(service)):
                resulttext = 'Attempt nr %d to start service %s host: %s was SUCCESSFUL' % (i,service,host)
                write_log("INFO", resulttext)
                send_mail(mail_user,mail_password,resulttext,subject,to)
                break
            else:
                resulttext = 'Attempt nr %d to start service %s host: %s was UNSUCCESSFUL' % (i,service,host)
                write_log("ERROR", resulttext)
                send_mail(mail_user,mail_password,resulttext,subject,to)
                time.sleep(freq)

#is_running function checks if service is running           
def is_running(service):
    cmd = 'service %s status' % (service)
    proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
    serviceStatus =  proc.communicate()[0]
    if "%s is running" %(service) in serviceStatus:
        print "INFO: Service is running"
        return True
    else:
        resulttext = 'Service %s is not running on host: %s' % (service,host)
        write_log("ERROR", resulttext)
        send_mail(mail_user,mail_password,resulttext,subject,to)
        return False

#start_service function attempts to start a service
def start_service(service):
    print 'INFO: Attemtping to start'
    cmd = 'service %s start' % (service)
    proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
    proc.communicate()

#sen_mail function sendes emails using predefined account   
def send_mail(mail_user,mail_password,body,subject,to):
    sent_from = mail_user
    msg = MIMEMultipart()
    msg['From'] = sent_from
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(mail_user, mail_password)
        mail_text = msg.as_string()
        server.sendmail(sent_from, to, mail_text)
        server.quit()
        write_log("INFO", "Mail notification sent")
    except:
        write_log("ERROR", "Failed to send mail notification")

#run_daemonized_watchdog functions runs watchdog in daemon mode
def run_daemonized_watchdog():
    resulttext = "Starting Watchdog as a Daemon"
    write_log("INFO", resulttext)
    with daemon.DaemonContext():
        run_watchdog()


#run_watchdog runs watchdog every 5 seconds
def run_watchdog():
    while True:
        watchdog(service,retry,freq)
        time.sleep(probing)

#starts the scrpt with check if script should be daemonized
if not (run_as_daemon):
    run_watchdog()
else:
    run_daemonized_watchdog()


