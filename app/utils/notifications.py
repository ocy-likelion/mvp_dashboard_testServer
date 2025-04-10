from dotenv import load_dotenv
import requests
import os
import logging

class SlackNotifier:
    def __init__(self):
        load_dotenv()  # 환경 변수 명시적 로딩
        self.logger = logging.getLogger(__name__)
        self.webhook_url = os.getenv('SLACK_WEBHOOK_URL')
        self.notice_channel = os.getenv('SLACK_CHANNEL', 'C08J05328D7')  # 공지사항용 채널
        self.issue_channel = os.getenv('SLACK_ISSUE_CHANNEL', 'C08LASRA397')  # 이슈용 채널
        
        # 초기화 시 환경 변수 확인
        if not self.webhook_url:
            print("ERROR: SLACK_WEBHOOK_URL이 설정되지 않았습니다!")
        if not self.notice_channel:
            print("ERROR: SLACK_CHANNEL이 설정되지 않았습니다!")
        if not self.issue_channel:
            print("ERROR: SLACK_ISSUE_CHANNEL이 설정되지 않았습니다!")
        
        self.logger.info(f"SlackNotifier 초기화: notice_channel={self.notice_channel}, issue_channel={self.issue_channel}")
        
    def send_notification(self, message, channel):
        try:
            if not self.webhook_url:
                logging.error("SLACK_WEBHOOK_URL이 설정되지 않았습니다.")
                return False
                
            payload = {
                "channel": channel,
                "text": message,
                "username": "Lion Helper Bot",
                "icon_emoji": ":lion_face:"
            }
            
            logging.info(f"Slack 알림 전송 시도 - Channel: {channel}")
            response = requests.post(self.webhook_url, json=payload)
            
            if response.status_code == 200:
                logging.info(f"Slack 알림 전송 성공 - Channel: {channel}")
                return True
            else:
                logging.error(f"Slack 알림 전송 실패: {response.status_code}, {response.text}")
                return False
        except Exception as e:
            logging.error(f"Slack 알림 전송 중 오류 발생: {str(e)}")
            return False

    def notify_new_notice(self, title, author):
        message = f"""
📢 *새로운 공지사항이 등록되었습니다!* \n 확인 후 *체크이모지*✅를 반드시 눌러주세요!
• 작성자: {author}
• 제목: {title}
"""
        return self.send_notification(message, self.notice_channel)

    def notify_new_issue(self, issue, author, training_course):
        message = f"""
⚠️ *새로운 이슈가 등록되었습니다!*
• 교육과정: {training_course}
• 작성자: {author}
• 내용: {issue}
"""
        return self.send_notification(message, self.issue_channel)

    def notify_new_comment(self, issue_title, author, training_course):
        message = f"""
💬 *새로운 댓글이 등록되었습니다!*
• 교육과정: {training_course}
• 이슈: {issue_title}
• 작성자: {author}
"""
        return self.send_notification(message, self.issue_channel)