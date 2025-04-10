from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os
import logging

class SlackNotifier:
    def __init__(self):
        self.client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
        self.channel = os.getenv('SLACK_CHANNEL', '#생산성제고_tf')
        
    def send_notification(self, message):
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message
            )
            return True
        except SlackApiError as e:
            logging.error(f"Slack 알림 전송 실패: {str(e)}")
            return False

    def notify_new_notice(self, title, author):
        message = f"📢 새로운 공지사항이 등록되었습니다!\n작성자: {author}\n제목: {title}"
        return self.send_notification(message)

    def notify_new_issue(self, title, author):
        message = f"⚠️ 새로운 이슈가 등록되었습니다!\n작성자: {author}\n제목: {title}"
        return self.send_notification(message)

    def notify_new_comment(self, issue_title, author):
        message = f"💬 새로운 댓글이 등록되었습니다!\n이슈: {issue_title}\n작성자: {author}"
        return self.send_notification(message)