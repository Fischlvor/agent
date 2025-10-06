"""邮件服务模块，提供邮件发送功能和HTML模板。"""

import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

from app.core.config import SETTINGS


class EmailService:
    """邮件服务类"""

    def __init__(self):
        self.host = SETTINGS.email_host
        self.port = SETTINGS.email_port
        self.from_email = SETTINGS.email_from
        self.nickname = SETTINGS.email_nickname
        self.password = SETTINGS.email_secret
        self.use_ssl = SETTINGS.email_is_ssl

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """发送邮件

        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            html_content: HTML邮件内容
            text_content: 纯文本内容（可选，作为HTML的备选）

        Returns:
            是否发送成功
        """
        try:
            # 创建邮件
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.nickname} <{self.from_email}>"
            message["To"] = to_email

            # 添加纯文本部分（如果有）
            if text_content:
                part1 = MIMEText(text_content, "plain", "utf-8")
                message.attach(part1)

            # 添加HTML部分
            part2 = MIMEText(html_content, "html", "utf-8")
            message.attach(part2)

            # 发送邮件
            server = None
            try:
                if self.use_ssl:
                    context = ssl.create_default_context()
                    server = smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=10)
                    server.login(self.from_email, self.password)
                    server.sendmail(self.from_email, to_email, message.as_string())
                else:
                    server = smtplib.SMTP(self.host, self.port, timeout=10)
                    server.starttls()
                    server.login(self.from_email, self.password)
                    server.sendmail(self.from_email, to_email, message.as_string())

                return True
            finally:
                if server:
                    try:
                        server.quit()
                    except:
                        pass
        except Exception as e:
            print(f"发送邮件失败: {e}")
            return False

    def send_verification_email(self, to_email: str, username: str, verification_link: str) -> bool:
        """发送注册验证邮件

        Args:
            to_email: 收件人邮箱
            username: 用户名
            verification_link: 验证链接

        Returns:
            是否发送成功
        """
        subject = "欢迎注册 Agent - 请验证您的邮箱"
        html_content = self._get_verification_email_template(username, verification_link)
        text_content = f"""
您好 {username}，

感谢您注册 Agent！

请点击以下链接验证您的邮箱：
{verification_link}

此链接将在24小时内有效。

如果您没有注册过账号，请忽略此邮件。

{SETTINGS.project_name} 团队
        """
        return self.send_email(to_email, subject, html_content, text_content)

    def send_login_code_email(self, to_email: str, username: str, code: str) -> bool:
        """发送登录验证码邮件

        Args:
            to_email: 收件人邮箱
            username: 用户名
            code: 6位验证码

        Returns:
            是否发送成功
        """
        subject = "您的登录验证码"
        html_content = self._get_login_code_email_template(username, code)
        text_content = f"""
您好 {username}，

您的登录验证码是：{code}

此验证码将在5分钟内有效，请尽快使用。

如果不是您本人操作，请忽略此邮件。

{SETTINGS.project_name} 团队
        """
        return self.send_email(to_email, subject, html_content, text_content)

    def send_password_reset_email(
        self,
        to_email: str,
        username: str,
        reset_link: str
    ) -> bool:
        """发送密码重置邮件

        Args:
            to_email: 收件人邮箱
            username: 用户名
            reset_link: 重置链接

        Returns:
            是否发送成功
        """
        subject = "重置您的密码"
        html_content = self._get_password_reset_email_template(username, reset_link)
        text_content = f"""
您好 {username}，

我们收到了您的密码重置请求。

请点击以下链接重置您的密码：
{reset_link}

此链接将在1小时内有效。

如果您没有请求重置密码，请忽略此邮件，您的密码将保持不变。

{SETTINGS.project_name} 团队
        """
        return self.send_email(to_email, subject, html_content, text_content)

    # ==================== HTML邮件模板 ====================

    def _get_verification_email_template(self, username: str, verification_link: str) -> str:
        """获取注册验证邮件的HTML模板"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>验证您的邮箱</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; border-radius: 8px 8px 0 0;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                {SETTINGS.project_name}
                            </h1>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="color: #333333; margin: 0 0 20px 0; font-size: 24px; font-weight: 600;">
                                欢迎加入, {username}! 👋
                            </h2>
                            <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                感谢您注册 <strong>{SETTINGS.project_name}</strong>。为了开始使用您的账户，请点击下方按钮验证您的邮箱地址。
                            </p>

                            <!-- Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{verification_link}" style="display: inline-block; padding: 14px 40px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);">
                                            验证邮箱
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="color: #999999; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0;">
                                如果按钮无法点击，请复制以下链接到浏览器地址栏：<br>
                                <a href="{verification_link}" style="color: #667eea; word-break: break-all;">{verification_link}</a>
                            </p>

                            <p style="color: #999999; font-size: 14px; line-height: 1.6; margin: 20px 0 0 0;">
                                ⏰ 此链接将在 <strong>24小时</strong> 内有效。
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9f9f9; padding: 30px; text-align: center; border-radius: 0 0 8px 8px;">
                            <p style="color: #999999; font-size: 13px; margin: 0; line-height: 1.5;">
                                如果您没有注册过账号，请忽略此邮件。<br>
                                © 2025 {SETTINGS.project_name}. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """

    def _get_login_code_email_template(self, username: str, code: str) -> str:
        """获取登录验证码邮件的HTML模板"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录验证码</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); padding: 40px 30px; text-align: center; border-radius: 8px 8px 0 0;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                {SETTINGS.project_name}
                            </h1>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px 30px; text-align: center;">
                            <h2 style="color: #333333; margin: 0 0 20px 0; font-size: 24px; font-weight: 600;">
                                您好, {username}! 🔐
                            </h2>
                            <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                您正在尝试登录 <strong>{SETTINGS.project_name}</strong>，请使用以下验证码完成登录。
                            </p>

                            <!-- Code Box -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center">
                                        <div style="display: inline-block; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px 60px; border-radius: 8px; margin: 20px 0;">
                                            <span style="color: #ffffff; font-size: 42px; font-weight: bold; letter-spacing: 10px; font-family: 'Courier New', monospace;">
                                                {code}
                                            </span>
                                        </div>
                                    </td>
                                </tr>
                            </table>

                            <p style="color: #ff6b6b; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0; font-weight: 600;">
                                ⏰ 此验证码将在 <strong>5分钟</strong> 内有效，请尽快使用。
                            </p>

                            <p style="color: #999999; font-size: 14px; line-height: 1.6; margin: 20px 0 0 0;">
                                如果不是您本人操作，请忽略此邮件，并建议您修改密码以确保账户安全。
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9f9f9; padding: 30px; text-align: center; border-radius: 0 0 8px 8px;">
                            <p style="color: #999999; font-size: 13px; margin: 0; line-height: 1.5;">
                                © 2025 {SETTINGS.project_name}. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """

    def _get_password_reset_email_template(self, username: str, reset_link: str) -> str:
        """获取密码重置邮件的HTML模板"""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>重置密码</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Arial, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 0;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 40px 30px; text-align: center; border-radius: 8px 8px 0 0;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                {SETTINGS.project_name}
                            </h1>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="color: #333333; margin: 0 0 20px 0; font-size: 24px; font-weight: 600;">
                                重置您的密码 🔑
                            </h2>
                            <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 10px 0;">
                                您好 <strong>{username}</strong>，
                            </p>
                            <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                我们收到了您的密码重置请求。点击下方按钮设置新密码。
                            </p>

                            <!-- Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="{reset_link}" style="display: inline-block; padding: 14px 40px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: #ffffff; text-decoration: none; border-radius: 6px; font-size: 16px; font-weight: 600; box-shadow: 0 4px 12px rgba(245, 87, 108, 0.4);">
                                            重置密码
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <p style="color: #999999; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0;">
                                如果按钮无法点击，请复制以下链接到浏览器地址栏：<br>
                                <a href="{reset_link}" style="color: #f5576c; word-break: break-all;">{reset_link}</a>
                            </p>

                            <p style="color: #ff6b6b; font-size: 14px; line-height: 1.6; margin: 20px 0 0 0; font-weight: 600;">
                                ⏰ 此链接将在 <strong>1小时</strong> 内有效。
                            </p>

                            <!-- Warning Box -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-top: 30px;">
                                <tr>
                                    <td style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 4px;">
                                        <p style="color: #856404; font-size: 14px; margin: 0; line-height: 1.5;">
                                            <strong>⚠️ 安全提示：</strong> 如果您没有请求重置密码，请忽略此邮件。您的密码将保持不变，账户仍然安全。
                                        </p>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9f9f9; padding: 30px; text-align: center; border-radius: 0 0 8px 8px;">
                            <p style="color: #999999; font-size: 13px; margin: 0; line-height: 1.5;">
                                © 2025 {SETTINGS.project_name}. All rights reserved.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """


# 创建全局邮件服务实例
email_service = EmailService()

