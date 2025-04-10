import requests
import os
import logging

class SlackNotifier:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.channel = os.getenv('SLACK_CHANNEL', '#생산성제고_tf')
        self.logger.info(f"SlackNotifier 초기화: channel={self.channel}")
        
    def send_notification(self, message):
        print("Slack 알림 전송 시작")
        if not self.webhook_url:
            print(f"SLACK_WEBHOOK_URL이 설정되지 않음: {self.webhook_url}")
            return False
            
        try:
            payload = {
                "channel": self.channel,
                "text": message,
                "username": "Lion Helper Bot",  # 봇 이름 설정
                "icon_emoji": ":lion_face:"     # 봇 아이콘 설정
            }
            
            print(f"Webhook 요청 전송 - Channel: {self.channel}")
            response = requests.post(self.webhook_url, json=payload)
            print(f"응답 상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                print("Webhook 요청 성공")
                return True
            else:
                print(f"Webhook 요청 실패: {response.text}")
                return False
        except Exception as e:
            print(f"알림 전송 중 오류 발생: {str(e)}")
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