"""This module contains logic for bug prediction service.

"""

def bugPrediction(changeSet):
    print "Running Bug Prediction Algorithm ..."
    outFileName = "/users/siasi/rankedVob.txt"
    file = open(outFileName)
    for line in file.readlines():
        if changeSet.coFiles.count(line.split(',')[0]):
            file.close()
            return "VERY HIGH"
    file.close()
    return "LOW"


def updateDescriptionWithBugPredition(descriptionFile):
    with open(descriptionFile, "r+") as f:
        old = f.read()
        if not old.startswith("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"):
            f.seek(0)
            f.write("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
            f.write("!!!!!!!!                    WARNING              !!!!!!!\n")
            f.write("!!!!!!! PROBABILITY TO INJECT A BUG IS VERY HIGH !!!!!!!\n")
            f.write("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
            f.write(old)
        f.close()

def predictBug(cs, description):
    prediction = bugPrediction(cs)
    if prediction == "VERY HIGH":
        print "Your change has high probability to inject a bug. Reviewers are notified with additional mail."
        updateDescriptionWithBugPredition(description)
    else:
        print "Probability to inject a bug for this code change is low."
    return prediction

def sendReport(send_to, subject, reportFile, reviewId, zipFile=""):
    '''Send a HTML report by mail.

    send_to is the address of the mail
    subject is the subject of the mail
    reportFile is the HTML report sent as body of the mail
    zipFile is the name of an optional zip file that is attached to the mail

    The mail is sent from the email address of the user running the function.

    An error message is printed in case of issues sending the mail.
    '''

    send_from = os.getenv('USER') + "@cisco.com"

    msg = MIMEMultipart()
    msg["From"] = "bugpredictor@cisco.com"
    msg["To"] = "daniemar@cisco.com,pacaruso@cisco.com"
    msg["Cc"] = "siasi@cisco.com"
    msg["Subject"] = subject
    msg['Date'] = formatdate(localtime=True)
    template = open(reportFile).read()
    message = template % (reviewId, reviewId, reviewId, reviewId)
    #print message
    #sys.exit(0)
    body = MIMEText(message, 'html')
    body['Content-Transfer-Encoding']='quoted-printable'

    msg.attach(body)

    if zipFile != "":
        attachment = MIMEBase('application', 'x-zip-compressed', name=os.path.basename(zipFile))
        attachment.set_payload(open(zipFile).read())
        encode_base64(attachment)
        msg.attach(attachment)

    server = smtplib.SMTP('localhost')

    try:
        failed = server.sendmail(send_from, [send_to], msg.as_string())
        server.close()
    except Exception, e:
        errorMsg = "Unable to send email. Error: %s" % str(e)
        print errorMsg
