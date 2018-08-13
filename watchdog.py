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
probing = 5
cfg = ConfigParser()
cfg.read('config.ini')
run_as_daemon = cfg.getboolean('daemonization','run_as_daemon')
logPath = cfg.get('logging','logPath')
freq = float(cfg.get('watchdog','time'))
retry = float(cfg.get('watchdog','retry'))
service = cfg.get('watchdog','service')
mail_user = cfg.get('notification','mail_user')
mail_password = cfg.get('notification','mail_password')
to = cfg.get('notification','to')
subject = cfg.get('notification','subject')
body = cfg.get('notification','body')


host = os.uname()[1]
#Setup logging file
if not os.path.exists(logPath):
        os.mknod(logPath)
logger = logging.getLogger ('watchdog')
hdlr = logging.FileHandler(logPath)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

#watchdog function restart service if it is down
def watchdog(service, retry, freq):
    if not (is_running(service)):
        i = 0
        while i < retry:
            i = i + 1
            logger.info('Attempt nr %d to start %s.' % (i,service))
            startService(service)
            if (is_running(service)):
                resulttext = 'Attempt nr %d to start service %s host: %s was SUCCESFUL' % (i,service,host)
                logger.info(resulttext)
                send_mail(mail_user,mail_password,resulttext,subject,to)
                break
            else:
                resulttext = 'Attempt nr %d to start service %s host: %s was UNSUCCESFUL' % (i,service,host)
                logger.error(resulttext)
                send_mail(mail_user,mail_password,resulttext,subject,to)
#Sleep for t seconds
            time.sleep(freq)

#is_running function checks if service is running           
def is_running(service):
    print ("Starting function is_running with paramter:" + service)
    cmd = 'service %s status' % (service)
    proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
    serviceStatus =  proc.communicate()[0]
    print serviceStatus
    if "%s is running" %(service) in serviceStatus:
        print "Service is running"
        return True
    else:
        resulttext = 'Service %s is not running on host: %s' % (service,host)
	time.sleep(time)
        logger.error(resulttext)
        send_mail(mail_user,mail_password,resulttext,subject,to)
	with open("/tmp/log.txt", "a") as f:
            f.write("The time is now " + time.ctime() + 'Service is not running')
        return False

#startService function attemts to start a service
def startService(service):
    print 'Attemtping to start'
    cmd = 'service %s start' % (service)
    proc = subprocess.Popen(cmd, shell=True,stdout=subprocess.PIPE)
    proc.communicate()


#sen_mail function sendes emails using prefedefined account   
def send_mail(mail_user,mail_password,body,subject,to):
    sent_from = mail_user
#    email_text = "Watchdog Alert: %s" %(body) 
    email_text = """ 
    From: %s  
    To: %s  
    Subject: %s
    %s
    """ % (sent_from, to, subject, body)
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        #server.ehlo()
        server.login(mail_user, mail_password)
        server.sendmail(sent_from, to, email_text)
        server.close()
        print 'Email sent!'
    except:
        print 'Something went wrong...'

#run_daemonized_watchdog functions runs watchdog in daemon mode
def run_daemonized_watchdog():
    with daemon.DaemonContext():
        run_watchdog()

#run_watchdog runs watchdog every 5 seconds
def run_watchdog()
     while True:
        watchdog(service,retry,freq)
        time.sleep(probing)

if not (run_as_daemon):
    run_watchdog()
else:
    run_daemonized_watchdog()


