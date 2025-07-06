import sys
import notify

mail_config = {
    "mail_host": "smtp.exmail.qq.com",
    "mail_port": 465,
    "mail_user": "",
    "mail_pass": "",
    "sender": "",
    "receivers": [""],
    "mail_notify": False,  # whether to send email notification
}

assert len(sys.argv) == 3, "Usage: python .test.py <mail_user> <mail_pass>"

mail_config["mail_user"] = sys.argv[1]
mail_config["mail_pass"] = sys.argv[2]
mail_config["sender"] = mail_config["mail_user"]
mail_config["receivers"] = [mail_config["mail_user"]] if mail_config["mail_user"] else []
if mail_config["mail_user"] and mail_config["mail_pass"]:
    mail_config["mail_notify"] = True

notify.mail_notification(
    mail_config=mail_config,
    subject="测试邮件通知",
    body="邮件通知测试，图片1：<img src='{img0}'>，图片2：<img src='{img1}'>",
    image_paths=["test/recent.png", "test/watts.png"],
)
