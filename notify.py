from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.header import Header
import smtplib

def mail_notification(mail_config, subject, body, image_paths=None):
    mail_host = mail_config["mail_host"]
    mail_port = mail_config["mail_port"]
    mail_user = mail_config["mail_user"]
    mail_pass = mail_config["mail_pass"]
    sender = mail_config["sender"]
    receivers = mail_config["receivers"]

    message = MIMEMultipart("related")
    message["From"] = Header(sender)

    if isinstance(receivers, list):
        message['To'] = Header(",".join(receivers), "utf-8")
    else:
        message['To'] = Header(receivers, "utf-8")
    message["Subject"] = Header(subject, "utf-8")

    # Attach the HTML body and inline images

    # Build HTML with <img> tags referencing Content-IDs
    html_body = body
    if image_paths is None:
        image_paths = []
    for idx, img_path in enumerate(image_paths):
        cid = f"image{idx}"
        # Replace placeholder in body with cid reference if needed
        html_body = html_body.replace(f"{{img{idx}}}", f"cid:{cid}")
        with open(img_path, "rb") as img_file:
            img = MIMEImage(img_file.read())
            img.add_header("Content-ID", f"<{cid}>")
            img.add_header("Content-Disposition", "inline", filename=img_path)
            message.attach(img)

    # Attach the HTML body
    message.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        smtp_obj = smtplib.SMTP_SSL(mail_host, mail_port)
        smtp_obj.login(mail_user, mail_pass)
        smtp_obj.sendmail(sender, receivers, message.as_string())
        smtp_obj.quit()
        return True
    except smtplib.SMTPException as e:
        print(f"SMTP error occurred: {e}")
        return False
