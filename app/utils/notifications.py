from dotenv import load_dotenv
import requests
import os
import logging

class SlackNotifier:
    def __init__(self):
        load_dotenv()  # 환경 변수 명시적 로딩
        self.logger = logging.getLogger(__name__)
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.channel = os.getenv('SLACK_CHANNEL')
        
        # 초기화 시 환경 변수 확인
        if not self.webhook_url:
            print("ERROR: SLACK_WEBHOOK_URL이 설정되지 않았습니다!")
        if not self.channel:
            print("ERROR: SLACK_CHANNEL이 설정되지 않았습니다!")
        
        self.logger.info(f"SlackNotifier 초기화: channel={self.channel}")
        
    def send_notification(self, message):
        try:
            if not self.webhook_url:
                print(f"Webhook URL이 없습니다: {os.getenv('SLACK_WEBHOOK_URL')}")
                return False

            payload = {
                "channel": self.channel,
                "text": message
            }

            print(f"Slack 알림 전송 시도: {payload}")
            response = requests.post(self.webhook_url, json=payload)
            print(f"Slack 응답: {response.status_code} - {response.text}")

            return response.status_code == 200
        except Exception as e:
            print(f"Slack 알림 전송 중 오류: {str(e)}")
            return False

    def notify_new_notice(self, title, author):
        message = f"""
📢 *새로운 공지사항이 등록되었습니다!*
• 작성자: {author}
• 제목: {title}
"""
        return self.send_notification(message)

    def notify_new_issue(self, title, author):
        message = f"""
⚠️ *새로운 이슈가 등록되었습니다!*
• 작성자: {author}
• 제목: {title}
"""
        return self.send_notification(message)

    def notify_new_comment(self, issue_title, author):
        message = f"""
💬 *새로운 댓글이 등록되었습니다!*
• 이슈: {issue_title}
• 작성자: {author}
"""
        return self.send_notification(message)