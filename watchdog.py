#!/bin/python

import sys
import subprocess
import time
import logging
import os
import smtplib
import daemon
from configparser import ConfigParser

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
#Sleep for t seconds
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
	time.sleep(freq)
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
#    email_text = "Watchdog Alert: %s" %(body) 
    email_text = """/
    From: %s  
    To: %s  
    Subject: %s
    %s
    """ % (sent_from, to, subject, body)
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(mail_user, mail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()
        print 'INFO: Email sent!'
    except:
        print 'ERROR: It was not possible to send mail please check configuration'

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


