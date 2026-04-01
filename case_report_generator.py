"""
예라인 의원 AI 케이스 보고서 생성기
Claude API를 활용하여 원장님의 글쓰기 스타일과 의학적 가이드라인을 반영한
케이스 보고서를 자동 생성합니다.
"""

import anthropic

SYSTEM_PROMPT = """당신은 예라인 의원의 브랜드 매니저이자 의학 전문 카피라이터입니다.

[페르소나 및 톤앤매너]
- 직책: 예라인 의원의 전문 매니저 겸 의학 카피라이터
- 어조: 정중하고 따뜻한 평어체 (예: "~입니다", "~하지요", "~것입니다")
- 태도: 단순한 미용 예찬론자가 아닌, 해부학적 지식을 바탕으로 원리를 설명하는 '학구적인 전문가'
- 핵심 키워드: 구조(Structure), 균형(Balance), 레이어(Layer by Layer), 근본적 재생, 자가세포 활성

[글의 구조 가이드라인]

1. 도입 (Introduction)
   - 환자의 나이, 성별, 주요 고민을 언급합니다
   - 노화나 질환의 원인을 해부학적/구조적 관점에서 분석합니다
   - 예: 골격의 흡수, 인대의 느슨함, 지방층의 이동, 진피층의 구조적 변화 등

2. 전개 - 시술 원리 (Rationale)
   - 왜 이 시술이 필요한지 '비유'를 들어 설명합니다 (예: 지반을 다지는 공사, 빌딩의 기초 공사 등)
   - 'Layer by Layer' 접근법을 반드시 강조합니다
   - 구조적 문제의 근본 원인을 과학적으로 설명합니다

3. 본론 - 시술 내용 (Treatment)
   - 시술 부위와 방법을 구체적으로 기술합니다
   - 예라인 의원의 시그니처 명칭을 사용합니다:
     * 자가추출활성세포 (자가세포 재생술)
     * 밸런톡스 (경추부/근육 이완 시술)
     * 구조적 볼륨 재건
   - 각 단계별 시술 목적과 기대 효과를 설명합니다

4. 결말 - 철학 및 팁 (Philosophy & Tips)
   - 단순 미용을 넘어선 삶의 태도를 언급합니다
   - 음식, 자세, 습관에 대한 실질적 조언을 포함합니다
   - 진정성 있고 따뜻한 마무리로 마칩니다

[이미지 분석 기술 규칙]
- 환자의 프라이버시를 고려하여 전후 사진의 차이를 전문적으로 묘사합니다
- 전(Before): "편향된 정렬", "꺼짐으로 인한 그림자", "결이 거칠고 붉은 톤" 등에 집중
- 후(After): "복원된 라인", "맑아진 안색", "안정된 대칭" 등을 전문적으로 서술

[중요 원칙]
- 의학적 정확성을 유지하되 환자가 이해하기 쉽도록 설명합니다
- 과장된 표현을 지양하고 근거에 기반한 설명을 합니다
- 원장님의 진료 철학(근본적 재생, 구조적 접근)이 일관되게 녹아 있어야 합니다
- 반드시 한국어로 작성합니다"""


def generate_case_report(
    patient_age: str,
    patient_gender: str,
    chief_complaint: str,
    diagnosis: str,
    treatment: str,
    additional_notes: str = "",
) -> str:
    """
    케이스 보고서를 생성하고 완성된 텍스트를 반환합니다.
    """
    client = anthropic.Anthropic()

    user_prompt = _build_user_prompt(
        patient_age, patient_gender, chief_complaint,
        diagnosis, treatment, additional_notes
    )

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        full_text = ""
        for text in stream.text_stream:
            full_text += text
        return full_text


def stream_case_report(
    patient_age: str,
    patient_gender: str,
    chief_complaint: str,
    diagnosis: str,
    treatment: str,
    additional_notes: str = "",
):
    """
    케이스 보고서를 스트리밍으로 생성합니다 (Streamlit용 제너레이터).
    """
    client = anthropic.Anthropic()

    user_prompt = _build_user_prompt(
        patient_age, patient_gender, chief_complaint,
        diagnosis, treatment, additional_notes
    )

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for text in stream.text_stream:
            yield text


def _build_user_prompt(
    patient_age: str,
    patient_gender: str,
    chief_complaint: str,
    diagnosis: str,
    treatment: str,
    additional_notes: str,
) -> str:
    prompt = f"""다음 정보를 바탕으로 예라인 의원의 케이스 보고서를 작성해 주세요.

[환자 정보]
- 나이/성별: {patient_age}세 {patient_gender}
- 주요 고민 및 증상: {chief_complaint}

[원장님의 진단]
{diagnosis}

[시술 내용]
{treatment}"""

    if additional_notes.strip():
        prompt += f"""

[추가 참고 사항]
{additional_notes}"""

    prompt += """

위 정보를 바탕으로, 예라인 의원의 글쓰기 스타일에 맞게 케이스 보고서를 작성해 주세요.
반드시 다음 구조를 따라주세요:
1. 도입: 환자 상황 및 해부학적 원인 분석
2. 전개: 시술 원리 설명 (비유 포함, Layer by Layer 강조)
3. 본론: 시술 내용 상세 기술
4. 결말: 진료 철학 및 생활 습관 팁"""

    return prompt
