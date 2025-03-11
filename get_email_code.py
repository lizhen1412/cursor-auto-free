#!/usr/bin/python3
# -*- coding: utf-8 -*-

from datetime import datetime
import logging
import time
import re
from config import Config
import requests
import email
import imaplib
import poplib
from email.parser import Parser


class EmailVerificationHandler:
    def __init__(self, account):
        """
        初始化邮件账户类

        :param account: 用户账户信息，用于登录邮件服务器
        """
        # 获取IMAP服务器配置
        self.imap = Config().get_imap()
        # 获取临时邮件账户用户名
        self.username = Config().get_temp_mail()
        # 获取临时邮件账户密码
        self.epin = Config().get_temp_mail_epin()
        # 初始化一个请求会话
        self.session = requests.Session()
        # 获取临时邮件地址的域名扩展
        self.emailExtension = Config().get_temp_mail_ext()
        # 获取协议类型，默认为 POP3
        self.protocol = Config().get_protocol() or 'POP3'
        # 保存用户账户信息
        self.account = account

    def get_verification_code(self, max_retries=5, retry_interval=60):
        """
        获取验证码，带有重试机制。

        Args:
            max_retries: 最大重试次数。
            retry_interval: 重试间隔时间（秒）。

        Returns:
            验证码 (字符串或 None)。
        """

        for attempt in range(max_retries):
            try:
                logging.info(f"尝试获取验证码 (第 {attempt + 1}/{max_retries} 次)...")

                if not self.imap:
                    verify_code, first_id = self._get_latest_mail_code()
                    if verify_code is not None and first_id is not None:
                        self._cleanup_mail(first_id)
                        return verify_code
                else:
                    if self.protocol.upper() == 'IMAP':
                        verify_code = self._get_mail_code_by_imap()
                    else:
                        verify_code = self._get_mail_code_by_pop3()
                    if verify_code is not None:
                        return verify_code

                if attempt < max_retries - 1:  # 除了最后一次尝试，都等待
                    logging.warning(f"未获取到验证码，{retry_interval} 秒后重试...")
                    time.sleep(retry_interval)

            except Exception as e:
                logging.error(f"获取验证码失败: {e}")  # 记录更一般的异常
                if attempt < max_retries - 1:
                    logging.error(f"发生错误，{retry_interval} 秒后重试...")
                    time.sleep(retry_interval)
                else:
                    raise Exception(f"获取验证码失败且已达最大重试次数: {e}") from e

        raise Exception(f"经过 {max_retries} 次尝试后仍未获取到验证码。")

    # 使用imap获取邮件
    def _get_mail_code_by_imap(self, retry = 0):
        if retry > 0:
            time.sleep(3)
        if retry >= 20:
            raise Exception("获取验证码超时")
        try:
            # 连接到IMAP服务器
            mail = imaplib.IMAP4_SSL(self.imap['imap_server'], self.imap['imap_port'])
            mail.login(self.imap['imap_user'], self.imap['imap_pass'])
            search_by_date=False
            # 针对网易系邮箱，imap登录后需要附带联系信息，且后续邮件搜索逻辑更改为获取当天的未读邮件
            if self.imap['imap_user'].endswith(('@163.com', '@126.com', '@yeah.net')):                
                imap_id = ("name", self.imap['imap_user'].split('@')[0], "contact", self.imap['imap_user'], "version", "1.0.0", "vendor", "imaplib")
                mail.xatom('ID', '("' + '" "'.join(imap_id) + '")')
                search_by_date=True
            mail.select(self.imap['imap_dir'])
            if search_by_date:
                date = datetime.now().strftime("%d-%b-%Y")
                status, messages = mail.search(None, f'ON {date} UNSEEN')
            else:
                status, messages = mail.search(None, 'TO', '"'+self.account+'"')
            if status != 'OK':
                return None

            mail_ids = messages[0].split()
            if not mail_ids:
                # 没有获取到，就在获取一次
                return self._get_mail_code_by_imap(retry=retry + 1)

            for mail_id in reversed(mail_ids):
                status, msg_data = mail.fetch(mail_id, '(RFC822)')
                if status != 'OK':
                    continue
                raw_email = msg_data[0][1]
                email_message = email.message_from_bytes(raw_email)

                # 如果是按日期搜索的邮件，需要进一步核对收件人地址是否对应
                if search_by_date and email_message['to'] !=self.account:
                    continue
                body = self._extract_imap_body(email_message)
                if body:
                    code_match = re.search(r"\b\d{6}\b", body)
                    if code_match:
                        code = code_match.group()
                        # 删除找到验证码的邮件
                        mail.store(mail_id, '+FLAGS', '\\Deleted')
                        mail.expunge()
                        mail.logout()
                        return code
            # print("未找到验证码")
            mail.logout()
            return None
        except Exception as e:
            print(f"发生错误: {e}")
            return None

    def _extract_imap_body(self, email_message):
        """
        提取邮件正文。

        遍历邮件的各个部分，寻找内容类型为"text/plain"且非附件的邮件正文部分。
        优先处理多部分邮件，对于非多部分邮件直接提取正文。

        参数:
        email_message: 邮件对象，包含邮件的原始内容。

        返回:
        邮件的正文文本。如果无法解码或找到合适的正文部分，则返回空字符串。
        """
        # 检查邮件是否为多部分组成
        if email_message.is_multipart():
            # 遍历邮件的每一个部分
            for part in email_message.walk():
                # 获取当前部分的内容类型和内容处置方式
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                # 寻找文本类型且非附件的部分
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    # 获取字符集，如果不存在则默认为utf-8
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        # 尝试解码并返回邮件正文
                        body = part.get_payload(decode=True).decode(charset, errors='ignore')
                        return body
                    except Exception as e:
                        # 如果解码失败，记录错误信息
                        logging.error(f"解码邮件正文失败: {e}")
        else:
            # 对于非多部分邮件，直接提取正文
            content_type = email_message.get_content_type()
            if content_type == "text/plain":
                charset = email_message.get_content_charset() or 'utf-8'
                try:
                    # 尝试解码并返回邮件正文
                    body = email_message.get_payload(decode=True).decode(charset, errors='ignore')
                    return body
                except Exception as e:
                    # 如果解码失败，记录错误信息
                    logging.error(f"解码邮件正文失败: {e}")
        # 如果没有找到合适的正文部分或解码失败，则返回空字符串
        return ""

    # 使用 POP3 获取邮件
    def _get_mail_code_by_pop3(self, retry = 0):
        """
        通过POP3协议获取邮件验证码。

        此函数尝试连接到POP3邮件服务器，检查最新的邮件以寻找由特定发件人发送的验证码。
        如果在当前邮件中没有找到验证码，它会递归地重试，直到找到验证码或超出最大重试次数。

        参数:
        retry (int): 重试次数，用于控制递归调用的次数，默认为0。

        返回:
        str: 验证码字符串，如果未找到则返回None。

        异常:
        如果重试次数超过20次仍未找到验证码，则抛出异常。
        """

        if retry > 0:
            time.sleep(3)
        if retry >= 20:
            raise Exception("获取验证码超时")
        
        pop3 = None
        try:
            # 连接到服务器
            pop3 = poplib.POP3_SSL(self.imap['imap_server'], int(self.imap['imap_port']))
            pop3.user(self.imap['imap_user'])
            pop3.pass_(self.imap['imap_pass'])
            
            # 获取最新的10封邮件
            num_messages = len(pop3.list()[1])
            for i in range(num_messages, max(1, num_messages-9), -1):
                response, lines, octets = pop3.retr(i)
                msg_content = b'\r\n'.join(lines).decode('utf-8')
                msg = Parser().parsestr(msg_content)
                
                # 检查发件人
                if 'no-reply@cursor.sh' in msg.get('From', ''):
                    # 提取邮件正文
                    body = self._extract_pop3_body(msg)
                    if body:
                        # 查找验证码
                        code_match = re.search(r"\b\d{6}\b", body)
                        if code_match:
                            code = code_match.group()
                            pop3.quit()
                            return code
            
            pop3.quit()
            return self._get_mail_code_by_pop3(retry=retry + 1)
            
        except Exception as e:
            print(f"发生错误: {e}")
            if pop3:
                try:
                    pop3.quit()
                except:
                    pass
            return None

    def _extract_pop3_body(self, email_message):
        """
        从email_message中提取POP3邮件的正文部分。

        如果邮件是多部分组成的，则遍历每个部分，寻找内容类型为"text/plain"且不是附件的部分作为正文。
        如果邮件不是多部分组成的，则直接提取邮件的负载作为正文。
        在提取正文的过程中，可能会遇到编码问题，因此使用try-except结构来捕获可能的异常，并记录错误日志。

        参数:
        email_message: 邮件对象，可以是单部分或多部分邮件。

        返回:
        返回提取到的邮件正文字符串，如果没有找到合适的正文部分，则返回空字符串。
        """
        # 提取邮件正文
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        return body
                    except Exception as e:
                        logging.error(f"解码邮件正文失败: {e}")
        else:
            try:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                return body
            except Exception as e:
                logging.error(f"解码邮件正文失败: {e}")
        return ""

    # 手动输入验证码
    def _get_latest_mail_code(self):
        """
        获取最新的邮件验证码和邮件ID。

        该方法首先请求邮件列表，然后获取列表中的最新邮件详情，
        最后使用正则表达式从邮件内容中提取6位数字的验证码。

        Returns:
            tuple: 包含验证码和邮件ID的元组。如果未找到验证码或邮件ID，则返回(None, None)。
        """
        # 获取邮件列表
        mail_list_url = f"https://tempmail.plus/api/mails?email={self.username}{self.emailExtension}&limit=20&epin={self.epin}"
        mail_list_response = self.session.get(mail_list_url)
        mail_list_data = mail_list_response.json()
        time.sleep(0.5)
        if not mail_list_data.get("result"):
            return None, None

        # 获取最新邮件的ID
        first_id = mail_list_data.get("first_id")
        if not first_id:
            return None, None

        # 获取具体邮件内容
        mail_detail_url = f"https://tempmail.plus/api/mails/{first_id}?email={self.username}{self.emailExtension}&epin={self.epin}"
        mail_detail_response = self.session.get(mail_detail_url)
        mail_detail_data = mail_detail_response.json()
        time.sleep(0.5)
        if not mail_detail_data.get("result"):
            return None, None

        # 从邮件文本中提取6位数字验证码
        mail_text = mail_detail_data.get("text", "")
        mail_subject = mail_detail_data.get("subject", "")
        logging.info(f"找到邮件主题: {mail_subject}")
        # 修改正则表达式，确保 6 位数字不紧跟在字母或域名相关符号后面
        code_match = re.search(r"(?<![a-zA-Z@.])\b\d{6}\b", mail_text)

        if code_match:
            return code_match.group(), first_id
        return None, None

    def _cleanup_mail(self, first_id):
        """
        删除邮件记录。

        本函数尝试通过API删除从给定ID开始的所有邮件记录。它会多次尝试以确保邮件记录被成功删除。

        参数:
        first_id (int): 需要删除的邮件序列的起始ID。

        返回:
        bool: 如果删除操作成功，则返回True，否则在尝试5次后返回False。
        """
        # 构造删除请求的URL和数据
        delete_url = "https://tempmail.plus/api/mails/"
        payload = {
            "email": f"{self.username}{self.emailExtension}",
            "first_id": first_id,
            "epin": f"{self.epin}",
        }

        # 最多尝试5次
        for _ in range(5):
            response = self.session.delete(delete_url, data=payload)
            try:
                result = response.json().get("result")
                if result is True:
                    return True
            except:
                pass

            # 如果失败,等待0.5秒后重试
            time.sleep(0.5)

        return False


if __name__ == "__main__":
    account = "test@gmail.com"
    # 创建EmailVerificationHandler实例并获取验证码
    email_handler = EmailVerificationHandler(account)
    # 获取验证码
    code = email_handler.get_verification_code()
    print(code)
