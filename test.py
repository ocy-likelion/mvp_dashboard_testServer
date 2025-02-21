import pickle
import re
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from konlpy.tag import Okt

# ✅ 1. ApplicationScorer 클래스 정의 (반드시 먼저 실행!)
import pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestRegressor
import re

class ApplicationScorer:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self._okt = None

        self.keywords = {
            'motivation':{
                'high':['목표', '계획', '비전', '열정', '구체적', '경험', '성장'],
                'medium':['관심', '희망', '배움', '도전'],
                'low':['취업', '스펙', '급여']
            },
            'capability':{
                'high':['프로젝트', '개발', '분석', '성과', '데이터', '결과', '아마존', 'EC2', '클라우드', 'Cloud'],
                'medium':['학습', '공부', '참여', '활동'],
                'low':['기초', '입문', '기본']
            },
            'growth':{
                'high':['달성', '목표', '계획', '구체적', '시간', '단계'],
                'medium':['성장', '발전', '향상', '습득'],
                'low':['시도', '희망', '노력']
            },
            'utilization':{
                'high':['취업', '실무', '적용', '활용', '구체적', '계획'],
                'medium':['학습', '이해', '습득'],
                'low':['희망', '관심', '노력']
            }
        }

    @property
    def okt(self):
        if self._okt is None:
            from konlpy.tag import Okt
            self._okt = Okt()
        return self._okt

    def __getstate__(self):
        # 피클링할 때는 _okt 객체를 제외
        state = self.__dict__.copy()
        state['_okt'] = None
        return state

    def __setstate__(self, state):
        # 피클 로드할 때는 _okt를 None으로 설정
        self.__dict__.update(state)

    def preprocess_text(self, text):
        text = re.sub(r'[^\w\s]', '', text)
        tokens = self.okt.morphs(text)
        return ''.join(tokens)

    def calculate_keyword_score(self, text, category):
        text = text.lower()
        score = 0

        for keyword in self.keywords[category]['high']:
            if keyword in text:
                score += 3
        for keyword in self.keywords[category]['medium']:
            if keyword in text:
                score += 2
        for keyword in self.keywords[category]['low']:
            if keyword in text:
                score += 1

        return score

    def evaluate_motivation(self, text):
        base_score = self.calculate_keyword_score(text, 'motivation')
        length_bonus = min(len(text) / 100, 5)
        specificity = len(re.findall(r'구체적|계획|목표|왜냐하면|때문에', text)) * 2
        total_score = min(base_score + length_bonus + specificity, 25)
        return total_score

    def evaluate_capability(self, text):
        base_score = self.calculate_keyword_score(text, 'capability')
        experience_bonus = len(re.findall(r'프로젝트|경험|결과', text)) * 3
        total_score = min(base_score + experience_bonus, 25)
        return total_score

    def evaluate_growth(self, text):
        base_score = self.calculate_keyword_score(text, 'growth')
        plan_bonus = len(re.findall(r'개월|주|일|시간|단계|계획', text)) * 3
        total_score = min(base_score + plan_bonus, 30)
        return total_score

    def evaluate_utilization(self, text):
        base_score = self.calculate_keyword_score(text, 'utilization')
        utilization_bonus = len(re.findall(r'취업|실무|적용|활용|계획', text)) * 2
        total_score = min(base_score + utilization_bonus, 20)
        return total_score

    def get_grade(self, score, max_score):
        percentage = (score / max_score) * 100
        if percentage >= 84:
            return 'A'
        elif percentage >= 64:
            return 'B'
        elif percentage >= 44:
            return 'C'
        else:
            return 'D'

    def evaluate_application(self, motivation_text, goal_text):
        motivation_score = self.evaluate_motivation(motivation_text)
        capability_score = self.evaluate_capability(motivation_text)
        growth_score = self.evaluate_growth(goal_text)
        utilization_score = self.evaluate_utilization(goal_text)

        total_score = motivation_score + capability_score + growth_score + utilization_score

        return {
            '참여 동기 및 의지':{
                '점수' : round(motivation_score, 2),
                '등급' : self.get_grade(motivation_score, 25)
            },
            '개인 역량':{
                '점수' : round(capability_score, 2),
                '등급' : self.get_grade(capability_score, 25)
            },
            '성장 가능성':{
                '점수' : round(growth_score, 2),
                '등급' : self.get_grade(growth_score, 30)
            },
            '교육 활용도':{
                '점수' : round(utilization_score, 2),
                '등급' : self.get_grade(utilization_score, 20)
            },
            '총점' : round(total_score, 2)
        }

# ✅ 2. 피클 파일 열기
MODEL_PATH = "models/application_scorer.pkl"

with open(MODEL_PATH, "rb") as file:
    model = pickle.load(file)

# ✅ 모델 정보 출력
print("✅ 모델 로드 성공:", type(model))
print(f"📌 모델 타입: {type(model)}")

# ✅ 4. 모델이 Pipeline인지 확인
if isinstance(model, Pipeline):
    print("\n🔹 모델이 Pipeline입니다. 각 단계 구성 요소:")
    for step_name, step_obj in model.named_steps.items():
        print(f"  - {step_name}: {type(step_obj)}")

    # ✅ 5. TfidfVectorizer 정보 확인
    if "tfidf" in model.named_steps:  # tfidf 단계가 있는지 확인
        vectorizer = model.named_steps["tfidf"]
        print("\n🔍 TfidfVectorizer 정보:")
        print("  - 최대 피처 개수:", vectorizer.max_features)
        print("  - 사용된 스톱워드:", vectorizer.stop_words)
        
        # ✅ 벡터라이저가 학습된 경우 단어 목록 출력
        if hasattr(vectorizer, "get_feature_names_out"):
            print("  - 사용된 단어 목록(일부):", vectorizer.get_feature_names_out()[:10])  # 일부만 출력

# ✅ 6. 모델의 하이퍼파라미터 출력
if hasattr(model, "get_params"):
    print("\n🔍 모델 하이퍼파라미터:")
    print(model.get_params())

# ✅ 7. 모델이 ApplicationScorer인지 확인
if isinstance(model, ApplicationScorer):
    print("\n🔍 모델이 ApplicationScorer입니다. 내부 속성:")
    print(dir(model))  # 내부 속성 목록 출력