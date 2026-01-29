# LearnIT 프로젝트 - 개인 기여 포트폴리오

## 📋 목차

1. [프로젝트 개요](#01-프로젝트-개요)
2. [기술 스택](#02-기술-스택)
3. [시스템 아키텍처](#03-시스템-아키텍처)
4. [데이터베이스 설계](#04-데이터베이스-설계)
5. [핵심 구현 상세](#05-핵심-구현-상세)
   - 5.1 [회원/인증 시스템](#51-회원인증-시스템)
     - 5.1.1 [소셜 로그인 및 회원가입](#511-소셜-로그인-및-회원가입)
     - 5.1.2 [일반 회원가입/로그인 및 인증 관리](#512-일반-회원가입로그인-및-인증-관리)
     - 5.1.3 [비밀번호 찾기 및 이메일 전송 시스템](#513-비밀번호-찾기-및-이메일-전송-시스템)
   - 5.2 [마이페이지 기능](#52-마이페이지-기능)
   - 5.3 [관리자 리뷰 관리 기능](#53-관리자-리뷰-관리-기능)
6. [주요 화면](#06-주요-화면)
7. [트러블 슈팅](#07-트러블-슈팅)
8. [성과 및 배운 점](#08-성과-및-배운-점)

---

# LearnIT 프로젝트

<span style="background-color: #0ea5e9; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 0.85em;">PROJECT</span> **LearnIT**

**Project Period**  
2025.12 - 2026.01 (6주) / 팀원 5명

**Project Role**  
백엔드/프론트엔드 개발

---

## [SERVICE OVERVIEW]

LearnIT는 강의 수강, 코드 실습, Q&A, 리뷰 작성 등 IT 온라인 교육에 필요한 모든 기능을 통합 제공하는 온라인 강의 플랫폼입니다. 온라인 교육에서 강의 수강과 코드 실습이 분리되어 학습 흐름이 끊기는 문제가 있죠. 본 서비스는 강의와 코드 실습을 통합하여 학습 흐름을 끊김 없이 제공하고, 학습자 간 협업 기능을 제공하여 온라인 교육의 한계를 극복합니다. 강의를 수강하면서 바로 코드를 실습하고, 질문하고, 리뷰를 작성할 수 있어 학습 효율을 높일 수 있죠.

---

## [WHAT I LEARNED]

팀 프로젝트에서 회원/인증 시스템과 마이페이지, 관리자 기능을 담당하면서 사용자 경험을 고려한 설계를 많이 고민했고, OAuth 소셜 로그인 통합과 권한별 데이터 필터링 등 복잡한 요구사항을 처리해야 하는 만큼 백엔드 설계 과정이 무척 즐거웠습니다. Provider별로 다른 OAuth 응답 구조를 통합 처리하고, 이메일 발송 실패 시 롤백하는 등 안전한 시스템을 설계하는 과정에서 많은 것을 배울 수 있었습니다. 또한, 팀원들과 협업하며 코드 리뷰와 브랜치 전략을 경험한 첫 팀 프로젝트라는 점에서 의미가 있습니다.

---

## 02. 기술 스택

### Backend
- **Java 17**
- **Spring Boot 3.x**
- **Spring Security** (인증/인가)
- **OAuth2 Client** (소셜 로그인)
- **MyBatis** (데이터베이스 매핑)
- **MySQL** (데이터베이스)
- **Thymeleaf** (템플릿 엔진)

### Frontend
- **HTML, CSS, JavaScript**
- **jQuery, Ajax** (비동기 통신)

### Infra
- **AWS** (EC2, S3, RDS)
- **Docker, Docker Compose**
- **Nginx**

---

## 03. 시스템 아키텍처

### 전체 시스템 구조

**시스템 아키텍처 다이어그램**:
```
┌─────────────────────────────────────────────────────────────────┐
│                         클라이언트 (브라우저)                      │
│                    HTML/CSS/JavaScript/jQuery                    │
└────────────────────────────┬────────────────────────────────────┘
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Nginx (리버스 프록시)                     │
│                    정적 파일 서빙, 로드 밸런싱                    │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Spring Boot 애플리케이션 (EC2)                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  프레젠테이션 계층                                        │  │
│  │  - Thymeleaf 템플릿 엔진                                  │  │
│  │  - Controller (REST API)                                  │  │
│  └──────────────────┬───────────────────────────────────────┘  │
│                     │                                           │
│  ┌──────────────────▼───────────────────────────────────────┐  │
│  │  비즈니스 계층                                            │  │
│  │  - Service Layer                                          │  │
│  │  - Spring Security (인증/인가)                            │  │
│  │  - OAuth2 Client (소셜 로그인)                            │  │
│  │  - Email Service (Gmail/Naver SMTP)                        │  │
│  └──────────────────┬───────────────────────────────────────┘  │
│                     │                                           │
│  ┌──────────────────▼───────────────────────────────────────┐  │
│  │  데이터 접근 계층                                          │  │
│  │  - MyBatis Mapper                                         │  │
│  │  - Repository Pattern                                     │  │
│  └──────────────────┬───────────────────────────────────────┘  │
└─────────────────────┼───────────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
┌───────────────┐         ┌──────────────────┐
│  MySQL (RDS)  │         │  AWS S3          │
│  - User       │         │  - 프로필 이미지  │
│  - Course     │         │  - 정적 파일      │
│  - Review     │         └──────────────────┘
│  - Cart       │
└───────────────┘

        ┌──────────────────────────────────┐
        │      외부 서비스 연동              │
        ├──────────────────────────────────┤
        │  • 카카오 OAuth2 API              │
        │  • 구글 OAuth2 API                │
        │  • Gmail SMTP                     │
        │  • Naver SMTP                     │
        └──────────────────────────────────┘
```

### 주요 컴포넌트

**프레젠테이션 계층**
- Thymeleaf 템플릿 엔진을 통한 서버 사이드 렌더링
- RESTful API를 통한 AJAX 통신
- jQuery를 활용한 클라이언트 사이드 로직

**비즈니스 계층**
- Spring Boot Service Layer에서 비즈니스 로직 처리
- Spring Security를 통한 인증/인가 관리
- OAuth2 Client를 통한 소셜 로그인 통합
- 이중화된 이메일 서비스 (Gmail/Naver)

**데이터 접근 계층**
- MyBatis를 통한 SQL 매핑 및 동적 쿼리 처리
- Repository Pattern을 통한 데이터 접근 추상화

**인프라 계층**
- **AWS EC2**: Spring Boot 애플리케이션 배포
- **AWS RDS**: MySQL 데이터베이스
- **AWS S3**: 프로필 이미지 및 정적 파일 저장
- **Docker**: 컨테이너화를 통한 배포 표준화
- **Nginx**: 리버스 프록시 및 정적 파일 서빙

### 배포 구조 (CI/CD 파이프라인)

**배포 아키텍처 다이어그램**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    개발자 로컬 환경 (Local Development)            │
│  ┌──────────────────────────┐  ┌──────────────────────────┐   │
│  │  Chat Agent 개발          │  │  Backend 개발            │   │
│  │  Python/FastAPI           │  │  Spring Boot             │   │
│  │  learnit-chat-agent       │  │  Acorn_Project_LearnIT   │   │
│  └───────────┬──────────────┘  └───────────┬──────────────┘   │
│              │                              │                   │
│              └──────────┬───────────────────┘                   │
│                         │ push release                          │
└─────────────────────────┼───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GitHub 저장소 (Repositories)                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │learnit-chat-agent│  │Acorn_Project_    │  │learnit-deploy│ │
│  │                  │  │LearnIT (Fork)    │  │              │ │
│  │• release branch  │  │• release branch  │  │• docker-     │ │
│  │• Dockerfile      │  │• Dockerfile      │  │  compose.yml │ │
│  │• GitHub Actions  │  │• GitHub Actions  │  │• nginx       │ │
│  └────────┬─────────┘  └────────┬─────────┘  │• certbot     │ │
│           │                     │             │(빌드 없음)    │ │
│           │ build & push        │             └──────┬───────┘ │
│           │ Docker images       │                    │         │
└───────────┼─────────────────────┼────────────────────┼─────────┘
            │                     │                    │
            │                     │                    │ git pull
            ▼                     ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Cloud (Amazon ECR)                        │
│  ┌──────────────────────┐  ┌──────────────────────┐           │
│  │learnit-chat-agent    │  │learnit-backend       │           │
│  │이미지                 │  │이미지                 │           │
│  └──────────────────────┘  └──────────────────────┘           │
└───────────────────────────────┬─────────────────────────────────┘
                                │ docker pull
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│              EC2 인스턴스 (Production Server)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Docker Compose                               │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │Spring Boot  │  │MySQL         │  │Chat Agent    │   │  │
│  │  │Container    │  │Container     │  │Container     │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Nginx Reverse Proxy / SSL                        │  │
│  │         • HTTP/HTTPS 요청 처리                            │  │
│  │         • SSL 인증서 관리 (Certbot)                      │  │
│  │         • 리버스 프록시 (→ Spring Boot Container)        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 배포 프로세스

1. **개발 단계**
   - 로컬 환경에서 Chat Agent (Python/FastAPI) 및 Backend (Spring Boot) 개발
   - `release` 브랜치에 코드 푸시

2. **CI/CD 단계 (GitHub Actions)**
   - `learnit-chat-agent` 및 `Acorn_Project_LearnIT` 저장소에서 자동 빌드 트리거
   - Dockerfile을 사용하여 Docker 이미지 빌드
   - 빌드된 이미지를 AWS ECR에 자동 푸시

3. **배포 단계**
   - `learnit-deploy` 저장소의 설정 파일들(docker-compose.yml, nginx, certbot)을 EC2에 git pull
   - AWS ECR에서 최신 Docker 이미지를 EC2로 docker pull
   - Docker Compose를 사용하여 다중 컨테이너 애플리케이션 실행
   - Nginx가 리버스 프록시 역할 및 SSL 인증서 관리

### 배포 환경 구성

- **컨테이너 오케스트레이션**: Docker Compose
- **CI/CD 도구**: GitHub Actions
- **컨테이너 레지스트리**: AWS ECR (Elastic Container Registry)
- **웹 서버**: Nginx (리버스 프록시, SSL 관리)
- **SSL 인증서**: Certbot (Let's Encrypt)

---

## 04. 데이터베이스 설계

### ERD (Entity Relationship Diagram) (추가 필요)
- 주요 엔티티: User, Course, Review, Cart, Order 등
- 엔티티 간 관계 및 외래키 제약조건

### 주요 테이블 구조

**User 테이블** (스크린샷 추가 권장)
- 주요 컬럼: user_id, email, password, provider, provider_id, status, role
- 인덱스: email (UNIQUE), provider + provider_id (복합 인덱스)

**Review 테이블** (스크린샷 추가 권장)
- 주요 컬럼: review_id, course_id, user_id, content, status, deleted
- 외래키: course_id → Course, user_id → User
- 인덱스: course_id, user_id, status

**admin_user_role 테이블** (스크린샷 추가 권장)
- 서브 어드민 권한 관리용 테이블
- 주요 컬럼: admin_id, course_id
- 복합 인덱스: admin_id + course_id

### 데이터베이스 설계 원칙
- 정규화를 통한 데이터 중복 최소화
- 인덱스 최적화를 통한 쿼리 성능 향상
- 소프트 삭제(deleted 플래그)를 통한 데이터 복구 가능
- 트랜잭션 관리를 통한 데이터 정합성 보장

---

## 05. 핵심 구현 상세

### 5.1 회원/인증 시스템

#### 5.1.1 소셜 로그인 및 회원가입

**로그인 구조 및 OAuth 필요성**
- **일반 로그인**: 사용자가 직접 이메일/비밀번호를 입력하여 인증 (자체 인증 시스템)
- **소셜 로그인**: 카카오, 구글 등 외부 서비스의 계정으로 로그인
  - **OAuth 2.0 필수**: 소셜 로그인을 구현하려면 OAuth 2.0 프로토콜을 사용해야 함
  - **이유**: 카카오/구글 등은 사용자의 비밀번호를 직접 제공하지 않고, OAuth 2.0을 통해 안전하게 인증 토큰만 발급
  - **OAuth 2.0 역할**: 사용자 인증을 외부 서비스(카카오, 구글)에 위임하고, 인증 성공 시 Access Token을 받아 사용자 정보를 조회하는 표준 프로토콜
- **구현 방식**: Spring Security OAuth2 Client를 사용하여 OAuth 2.0 프로토콜 구현

**OAuth 2.0 소셜 로그인 구현 구조**:
```
┌─────────────────────────────────────────────────────────────────┐
│                    OAuth 2.0 인증 흐름                            │
└─────────────────────────────────────────────────────────────────┘

[1단계: 사용자 요청]
사용자 → LearnIT 서버
  "카카오로 로그인" 버튼 클릭
  ↓
  GET /oauth2/authorization/kakao

[2단계: 인증 서버로 리다이렉트]
LearnIT 서버 → 카카오 인증 서버
  Authorization Request
  (client-id, redirect-uri, scope 등)
  ↓
  사용자가 카카오에서 로그인 및 동의

[3단계: 인증 코드 발급]
카카오 인증 서버 → LearnIT 서버
  GET /login/oauth2/code/kakao?code={authorization_code}
  (인증 코드 전달)

[4단계: Access Token 교환]
LearnIT 서버 → 카카오 인증 서버
  POST /oauth/token
  (authorization_code + client-secret)
  ↓
  Access Token 발급

[5단계: 사용자 정보 조회]
LearnIT 서버 → 카카오 API 서버
  GET /v2/user/me
  (Access Token 포함)
  ↓
  사용자 정보 응답 (id, email, profile 등)

[6단계: 사용자 처리]
LearnIT 서버 내부 처리
  ├─ OAuthService.loadUser()
  │   └─ extractOAuthUserInfo() → OAuthUserDTO 변환
  ├─ findOrCreateUser()
  │   └─ 기존 사용자 조회 또는 신규 생성
  └─ 세션 생성 및 로그인 완료

┌─────────────────────────────────────────────────────────────────┐
│              구현한 코드 순서 및 구조                            │
└─────────────────────────────────────────────────────────────────┘

[1단계: OAuth2 설정 구성] (SecurityConfig.java)
  └─ oauth2Login() 설정
      ├─ userService(oAuthService) 등록
      └─ successHandler(oAuth2LoginSuccessHandler) 등록

[2단계: OAuthService 구현] (OAuthService.java)
  └─ DefaultOAuth2UserService 상속
      └─ loadUser() 메서드 오버라이드
          ├─ Step 1: super.loadUser() 호출
          │   ├─ 구글: 예외 처리 (sub null 체크)
          │   │   └─ 예외 발생 시 loadGoogleUserDirectly() 호출
          │   └─ 카카오: 기본 방식 사용
          │
          ├─ Step 2: extractOAuthUserInfo() 호출
          │   └─ Provider별 분기 처리
          │       ├─ 구글: 평면 구조 추출
          │       └─ 카카오: 중첩 구조 추출
          │       └─ → OAuthUserDTO 변환
          │
          └─ Step 3: findOrCreateUser() 호출
              ├─ provider + providerId로 기존 사용자 조회
              ├─ 없으면 email로 기존 사용자 조회 (자동 연동)
              └─ 없으면 신규 사용자 생성 (STATUS_SIGNUP_PENDING)

[3단계: 로그인 성공 후 처리] (OAuth2LoginSuccessHandler.java)
  └─ onAuthenticationSuccess() 메서드
      ├─ 사용자 조회 (provider + providerId 또는 email)
      ├─ STATUS_SIGNUP_PENDING 체크
      │   └─ PENDING이면 /user/additional-info로 리다이렉트
      ├─ 세션 생성 (setLoginSession)
      ├─ 게스트 장바구니 병합
      └─ 최종 리다이렉트 처리

┌─────────────────────────────────────────────────────────────────┐
│              Spring Security OAuth2 Client 구조                   │
└─────────────────────────────────────────────────────────────────┘

[설정 파일] application.yml
  spring:
    security:
      oauth2:
        client:
          registration:
            kakao:
              client-id: {카카오 앱 키}
              client-secret: {카카오 시크릿 키}
              redirect-uri: /login/oauth2/code/kakao
            google:
              client-id: {구글 클라이언트 ID}
              client-secret: {구글 시크릿 키}
              redirect-uri: /login/oauth2/code/google

[컴포넌트 구조]
  SecurityConfig
    └─ OAuth2LoginConfigurer
        └─ OAuth2LoginSuccessHandler (로그인 성공 후 처리)
            └─ OAuthService (DefaultOAuth2UserService 상속)
                ├─ loadUser() - 사용자 정보 로드
                ├─ extractOAuthUserInfo() - Provider별 데이터 추출
                └─ findOrCreateUser() - 사용자 찾기/생성
```

- **OAuth 소셜 로그인 통합 처리**

  **배경**
  ```
  Spring Security OAuth2 Client로 카카오/구글 로그인 구현
  → OAuth 인증 흐름은 표준화되어 있으나, 사용자 정보 응답 구조는 Provider별로 다름
  ```

  **문제점 → 해결책 (통합 처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │                    OAuth 소셜 로그인 통합 처리 흐름                    │
  └─────────────────────────────────────────────────────────────────────┘
  
  [시작] 사용자가 소셜 로그인 클릭
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제 2: 구글 sub null 예외 발생                                       │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 일부 구글 계정에서 sub 값이 null로 반환
        │   → Spring Security가 사용자 식별자로 사용 불가
        │   → IllegalArgumentException 발생, 로그인 실패
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결 2: 구글 sub null 예외 처리                                       │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ loadUser() 호출
        │       │
        │       ├─→ [구글인 경우]
        │       │       │
        │       │       ├─→ super.loadUser() 시도
        │       │       │       │
        │       │       │       ├─→ [성공] → OAuth2User 반환
        │       │       │       │
        │       │       │       └─→ [예외: 'sub' cannot be null]
        │       │       │               │
        │       │       │               ▼
        │       │       │           loadGoogleUserDirectly() 호출
        │       │       │               │
        │       │       │               ├─→ 구글 API 직접 호출
        │       │       │               ├─→ sub 없으면 id 사용
        │       │       │               └─→ 없으면 email 기반 생성
        │       │       │
        │       │       └─→ [카카오인 경우] → super.loadUser() 정상 처리
        │       │
        │       └─→ OAuth2User 획득 완료
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제 1: 응답 구조 차이로 인한 통합 처리 어려움                        │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 카카오: 중첩 구조 (id → kakao_account → profile)
        │   구글:   평면 구조 (sub, email, name, picture)
        │   → 동일한 방식으로 추출 불가, Provider별 별도 코드 필요
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결 1: Provider별 분기 처리                                         │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ extractOAuthUserInfo(OAuth2User, registrationId) 호출
        │       │
        │       ├─→ registrationId 확인
        │       │       │
        │       ├─→ [구글인 경우]
        │       │       │
        │       │       ├─→ 평면 구조 직접 추출
        │       │       │   ├─→ getAttribute("sub") → providerId
        │       │       │   ├─→ getAttribute("email") → email
        │       │       │   ├─→ getAttribute("name") → name
        │       │       │   └─→ getAttribute("picture") → profileImg
        │       │       │
        │       └─→ [카카오인 경우]
        │               │
        │               ├─→ 중첩 구조 단계별 추출
        │               │   ├─→ getAttribute("id") → providerId
        │               │   ├─→ getAttribute("kakao_account") → Map
        │               │   │   ├─→ get("email") → email
        │               │   │   └─→ get("profile") → Map
        │               │   │       ├─→ get("nickname") → name
        │               │   │       └─→ get("profile_image_url") → profileImg
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결 3: 공통 DTO 패턴 적용 (문제 1의 추가 해결)                        │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ Provider별로 다른 구조의 데이터
        │       │
        │       └─→ OAuthUserDTO로 통합
        │               ├─→ provider (구글/카카오)
        │               ├─→ providerId
        │               ├─→ email
        │               ├─→ name
        │               └─→ profileImg
        │
        │   → 이후 로직은 Provider 무관하게 공통 DTO만 사용
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결 4: 이메일 기반 계정 자동 연동 (사용자 경험 개선)                  │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ findOrCreateUser(provider, providerId, email) 호출
        │       │
        │       ├─→ [1단계] provider + providerId로 조회
        │       │       │
        │       │       ├─→ [기존 사용자 있음] → 기존 사용자 반환
        │       │       │
        │       │       └─→ [없음]
        │       │               │
        │       │               ▼
        │       │       [2단계] email로 조회
        │       │               │
        │       │               ├─→ [기존 사용자 있음]
        │       │               │       │
        │       │               │       └─→ 자동 연동 (기존 사용자 반환)
        │       │               │           → 같은 이메일로 다른 Provider 로그인 시 자동 연동
        │       │               │
        │       │               └─→ [없음]
        │       │                       │
        │       │                       ▼
        │       │               [3단계] 신규 사용자 생성
        │       │                       │
        │       │                       ├─→ STATUS_SIGNUP_PENDING 상태로 저장
        │       │                       ├─→ 환영 이메일 발송
        │       │                       └─→ 신규 사용자 반환
        │
        ▼
  [완료] 로그인 성공 / 회원가입 완료
  ```

  **핵심 코드**:
  ```java
  // 해결 2: 구글 sub null 예외 처리
  @Override
  public OAuth2User loadUser(OAuth2UserRequest userRequest) {
      String registrationId = userRequest.getClientRegistration().getRegistrationId();
      if ("google".equals(registrationId)) {
          try {
              return super.loadUser(userRequest);
          } catch (IllegalArgumentException e) {
              if (e.getMessage().contains("'sub' cannot be null")) {
                  return loadGoogleUserDirectly(userRequest);
              }
              throw e;
          }
      }
      return super.loadUser(userRequest);
  }
  
  // 해결 1: Provider별 분기 처리
  private OAuthUserDTO extractOAuthUserInfo(OAuth2User oAuth2User, String registrationId) {
      if ("google".equals(registrationId)) {
          return OAuthUserDTO.builder()
              .providerId(oAuth2User.getAttribute("sub"))
              .email(oAuth2User.getAttribute("email"))
              .name(oAuth2User.getAttribute("name"))
              .build();
      } else if ("kakao".equals(registrationId)) {
          Map<String, Object> kakaoAccount = oAuth2User.getAttribute("kakao_account");
          Map<String, Object> profile = (Map<String, Object>) kakaoAccount.get("profile");
          return OAuthUserDTO.builder()
              .providerId(oAuth2User.getAttribute("id"))
              .email((String) kakaoAccount.get("email"))
              .name((String) profile.get("nickname"))
              .build();
      }
      return null;
  }
  
  // 해결 4: 이메일 기반 계정 연동
  private User findOrCreateUser(String provider, String providerId, String email) {
      // 1단계: provider + providerId로 조회
      User user = userRepository.findByProviderAndProviderId(provider, providerId);
      if (user != null) return user;
      
      // 2단계: email로 조회 (자동 연동)
      user = userRepository.findByEmail(email);
      if (user != null) return user;
      
      // 3단계: 신규 사용자 생성
      return createNewUser(provider, providerId, email);
  }
  ```

- **소셜 회원가입 후 추가 정보 입력**

  **문제점 → 해결책 (처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제: 소셜 로그인 시 필수 정보 부족                                  │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 소셜 로그인은 이메일, 이름만 제공
        │   → 닉네임, 전화번호, 지역, GitHub URL 등 필수 정보 부족
        │   → 추가 정보 없이는 서비스 이용 불가
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결: STATUS_SIGNUP_PENDING 상태 관리 및 추가 정보 입력 프로세스      │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [1단계] 신규 사용자 생성
        │       │
        │       ├─→ STATUS_SIGNUP_PENDING 상태로 저장
        │       ├─→ 환영 이메일 발송 (Gmail → Naver 재시도)
        │       └─→ 추가 정보 입력 페이지로 리다이렉트
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결: 인터셉터를 통한 접근 제어                                       │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ STATUS_SIGNUP_PENDING 상태 사용자
        │       │
        │       ├─→ 추가 정보 입력 페이지 → 접근 허용
        │       └─→ 다른 페이지 → 접근 차단 (리다이렉트)
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결: 추가 정보 입력 및 자동 포맷팅                                  │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 사용자가 추가 정보 입력
        │       │
        │       ├─→ 닉네임, 전화번호, 지역 입력
        │       ├─→ GitHub URL 입력 (사용자명만 입력해도 자동 포맷팅)
        │       │   예: "username" → "https://github.com/username"
        │       │
        │       └─→ 추가 정보 저장
        │               │
        │               ├─→ STATUS_ACTIVE로 상태 변경
        │               ├─→ 세션 갱신
        │               └─→ 서비스 이용 가능
        │
        ▼
  [완료] 소셜 회원가입 및 추가 정보 입력 완료
  ```

  **핵심 코드**:
  ```java
  // 신규 사용자 생성 및 PENDING 상태 설정
  @Transactional
  private User findOrCreateUser(OAuthUserDTO oauthUser, String registrationId) {
      User newUser = new User();
      newUser.setStatus(User.STATUS_SIGNUP_PENDING); // 추가 정보 입력 대기
      newUser = userRepository.save(newUser);
      
      // 환영 이메일 발송
      emailService.sendWelcomeEmail(newUser.getEmail(), newUser.getName());
      return newUser;
  }

  // 추가 정보 입력 완료
  @PostMapping("/user/additional-info")
  public String submitAdditionalInfo(
          @RequestParam String nickname,
          @RequestParam String phone,
          @RequestParam String region,
          @RequestParam(required = false) String githubUrl,
          HttpSession session) {
      
      // GitHub URL 자동 포맷팅
      if (githubUrl != null && !githubUrl.startsWith("http")) {
          githubUrl = "https://github.com/" + githubUrl;
      }
      
      // 추가 정보 업데이트 및 상태 변경
      userService.updateAdditionalInfo(userId, nickname, phone, region, githubUrl);
      
      // 세션 갱신
      User updatedUser = userService.getUserById(userId);
      sessionService.setLoginSession(session, updatedUser);
      
      return "redirect:/home";
  }
  ```

#### 5.1.2 일반 회원가입/로그인 및 인증 관리

- **일반 회원가입/로그인**

  **문제점 → 해결책 (처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제 1: 비밀번호 보안 및 이메일 중복 처리                           │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 평문 비밀번호 저장 시 보안 취약
        │   → 이메일 중복 가입 방지 필요
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결 1: 이메일 중복 검증 및 BCrypt 암호화                             │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [회원가입 프로세스]
        │       │
        │       ├─→ 이메일 중복 체크
        │       │       │
        │       │       ├─→ [중복] → 에러 반환
        │       │       │
        │       │       └─→ [가능] → 비밀번호 BCrypt 암호화
        │       │               │
        │       │               ├─→ 사용자 저장 (STATUS_ACTIVE)
        │       │               ├─→ 환영 이메일 발송
        │       │               └─→ 회원가입 완료
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제 2: 게스트 장바구니 데이터 손실                                   │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 로그인 전 게스트로 장바구니에 담은 강의
        │   → 로그인 후 장바구니 데이터 손실
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결 2: 세션 생성 및 게스트 장바구니 자동 병합                        │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [로그인 프로세스]
        │       │
        │       ├─→ 인증 검증 (이메일/비밀번호)
        │       │       │
        │       │       ├─→ [실패] → 로그인 실패
        │       │       │
        │       │       └─→ [성공]
        │       │               │
        │       │               ├─→ 세션 생성 (USER_ID, ROLE 저장)
        │       │               │
        │       │               └─→ 게스트 장바구니 확인
        │       │                       │
        │       │                       ├─→ [있음] → 장바구니 병합
        │       │                       │
        │       │                       └─→ [없음] → 홈으로 이동
        │
        ▼
  [완료] 로그인 성공 및 장바구니 데이터 보존
  ```

  **핵심 코드**:
  ```java
  // 회원가입 - 이메일 중복 체크 및 BCrypt 암호화
  @Transactional
  public User signup(SignupRequestDTO request) {
      if (userRepository.existsByEmail(request.getEmail())) {
          throw new IllegalArgumentException("이미 사용 중인 이메일입니다.");
      }
      
      User newUser = new User();
      newUser.setPassword(passwordEncoder.encode(request.getPassword())); // BCrypt
      newUser.setStatus(User.STATUS_ACTIVE);
      newUser = userRepository.save(newUser);
      
      emailService.sendWelcomeEmail(newUser.getEmail(), newUser.getName());
      return newUser;
  }

  // 로그인 - 세션 생성 및 장바구니 병합
  @PostMapping("/login")
  public String doLogin(@RequestParam String email, @RequestParam String password,
                       HttpSession session, Model model) {
      User user = userService.login(email, password);
      if (user == null) {
          model.addAttribute("error", "이메일 또는 비밀번호가 맞지 않습니다.");
          return "user/login";
      }
      
      // 세션 생성
      userService.setLoginSession(session, user);
      
      // 게스트 장바구니 병합
      List<Long> guestCourseIds = (List<Long>) session.getAttribute("GUEST_CART_COURSE_IDS");
      if (guestCourseIds != null && !guestCourseIds.isEmpty()) {
          cartService.mergeGuestCartToUser(user.getUserId(), guestCourseIds);
      }
      
      return "redirect:/home";
  }
  ```

- **세션 기반 인증 관리**

  **문제점 → 해결책 (처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제: 인증되지 않은 사용자의 관리자 페이지 접근                      │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 관리자 페이지는 인증 및 권한 필요
        │   → Open Redirect 공격 방지 필요
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결: 인터셉터를 통한 인증/권한 체크                                  │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [요청 접근]
        │       │
        │       ├─→ 인터셉터 preHandle() 실행
        │       │       │
        │       │       ├─→ [관리자 페이지 (/admin)]
        │       │       │       │
        │       │       │       ├─→ 세션 존재 확인
        │       │       │       │       │
        │       │       │       │       ├─→ [없음] → 로그인 페이지 리다이렉트
        │       │       │       │       │
        │       │       │       │       └─→ [있음] → 권한 체크
        │       │       │       │               │
        │       │       │       │               ├─→ [ADMIN/SUB_ADMIN] → 접근 허용
        │       │       │       │               │
        │       │       │       │               └─→ [일반 사용자] → 권한 없음 리다이렉트
        │       │       │       │
        │       │       └─→ [일반 페이지]
        │       │               │
        │       │               ├─→ 세션 존재 → 세션 정보 사용
        │       │               │
        │       │               └─→ 세션 없음 → 게스트 접근 허용
        │
        ▼
  [완료] 권한별 접근 제어 완료
  ```

  **핵심 코드**:
  ```java
  // 세션 관리
  public void setLoginSession(HttpSession session, User user) {
      session.setAttribute("LOGIN_USER_ID", user.getUserId());
      session.setAttribute("LOGIN_USER_NAME", user.getName());
      session.setAttribute("LOGIN_USER_ROLE", user.getRole());
  }
  
  // 인터셉터 - 인증/권한 체크
  @Override
  public boolean preHandle(HttpServletRequest request, HttpServletResponse response, 
                          Object handler) throws Exception {
      if (request.getRequestURI().startsWith("/admin")) {
          HttpSession session = request.getSession(false);
          if (session == null || session.getAttribute("LOGIN_USER_ID") == null) {
              response.sendRedirect("/login");
              return false;
          }
          
          String role = (String) session.getAttribute("LOGIN_USER_ROLE");
          if (role == null || (!"ADMIN".equals(role) && !"SUB_ADMIN".equals(role))) {
              response.sendRedirect("/home?error=unauthorized");
              return false;
          }
      }
      return true;
  }
  ```

// 인터셉터 - 인증 체크
@Override
public boolean preHandle(HttpServletRequest request, HttpServletResponse response, 
                        Object handler) throws Exception {
    HttpSession session = request.getSession(false);
    
    // 관리자 페이지 접근 제어
    if (requestURI.startsWith("/admin")) {
        if (session == null || session.getAttribute("LOGIN_USER_ID") == null) {
            response.sendRedirect("/login");
            return false;
        }
        
        // 권한 체크
        String role = (String) session.getAttribute("LOGIN_USER_ROLE");
        if (role == null || (!"ADMIN".equals(role) && !"SUB_ADMIN".equals(role))) {
            response.sendRedirect("/home?error=unauthorized");
            return false;
        }
    }
    
    return true;
}
```

- **권한별 데이터 필터링**

  **문제점 → 해결책 (처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제: 관리자, 서브 어드민, 일반 사용자별 조회 권한 차이                │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 관리자: 모든 데이터 조회 가능
        │   서브 어드민: 관리하는 강의의 데이터만 조회
        │   일반 사용자: 본인 데이터만 조회
        │   → 권한별로 다른 쿼리 필요
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결: 동적 SQL을 활용한 권한별 필터링                                 │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [데이터 조회 프로세스]
        │       │
        │       ├─→ 사용자 권한 확인
        │       │       │
        │       │       ├─→ [ADMIN] → 전체 데이터 조회
        │       │       │
        │       │       ├─→ [SUB_ADMIN]
        │       │       │       │
        │       │       │       ├─→ admin_user_role 테이블에서 관리 강의 ID 조회
        │       │       │       ├─→ 관리 강의 ID 목록 추출
        │       │       │       └─→ 동적 SQL 생성 (IN 절 필터링)
        │       │       │
        │       │       └─→ [일반 사용자] → 본인 데이터만 조회
        │       │
        │       └─→ MyBatis 동적 쿼리 실행
        │               │
        │               └─→ 권한별 필터링된 데이터 반환
        │
        ▼
  [완료] 권한별 필터링된 데이터 반환
  ```

#### 5.1.3 비밀번호 찾기 및 이메일 전송 시스템

- **비밀번호 찾기 기능**

  **문제점 → 해결책 (처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제 1: 비밀번호 분실 시 계정 복구 불가                               │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 사용자가 비밀번호를 잊어버림
        │   → 계정 접근 불가
        │   → 소셜 로그인 사용자는 비밀번호가 없음
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결 1: 사용자 검증 및 임시 비밀번호 발송 시스템                      │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [비밀번호 찾기 프로세스]
        │       │
        │       ├─→ 사용자 검증
        │       │       │
        │       │       ├─→ [소셜 로그인 사용자] → 비밀번호 찾기 불가 처리
        │       │       │
        │       │       └─→ [일반 사용자]
        │       │               │
        │       │               ├─→ 8자리 임시 비밀번호 생성 (영문+숫자)
        │       │               │
        │       │               └─→ 이메일 발송 시도
        │       │                       │
        │       │                       ├─→ [발송 실패] → 롤백 (비밀번호 변경 안함)
        │       │                       │
        │       │                       └─→ [발송 성공]
        │       │                               │
        │       │                               ├─→ BCrypt 암호화
        │       │                               └─→ DB에 임시 비밀번호 저장
        │
        ▼
  [완료] 임시 비밀번호 이메일 발송 완료
  ```

  **핵심 코드**:
  ```java
  // 비밀번호 찾기 - 트랜잭션 안전성 보장
  @PostMapping("/user/find-password")
  public String findPassword(@RequestParam String email, Model model) {
      String tempPassword = userService.preparePasswordReset(email);
      
      if (tempPassword != null) {
          try {
              // 이메일 발송 성공 시에만 비밀번호 변경
              emailService.sendTempPasswordEmail(email, tempPassword);
              userService.resetPassword(email, tempPassword);
              model.addAttribute("success", "임시 비밀번호가 이메일로 발송되었습니다.");
          } catch (Exception e) {
              // 이메일 발송 실패 시 롤백
              model.addAttribute("error", "이메일 발송에 실패했습니다.");
          }
      }
      return "user/findPassword";
  }
  ```

- **이메일 전송 시스템**

  **문제점 → 해결책 (처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제: 단일 SMTP 서버 장애 시 이메일 발송 실패                         │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ Gmail SMTP만 사용 시
        │   → Gmail 장애 발생 시 모든 이메일 발송 실패
        │   → 회원가입 프로세스 중단 가능성
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결: Gmail/Naver 이중화 구조 및 예외 처리                            │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [이메일 발송 프로세스]
        │       │
        │       ├─→ [1단계] Gmail SMTP 우선 시도
        │       │       │
        │       │       ├─→ [성공] → 이메일 발송 완료
        │       │       │
        │       │       └─→ [실패]
        │       │               │
        │       │               ▼
        │       │       [2단계] Naver SMTP 재시도
        │       │               │
        │       │               ├─→ [성공] → 이메일 발송 완료
        │       │               │
        │       │               └─→ [실패] → 예외 처리 (로깅만 수행)
        │       │                       │
        │       │                       └─→ 프로세스 계속 진행 (회원가입 중단 안함)
        │
        ▼
  [완료] 이메일 발송 완료 또는 실패 처리
  ```

  **핵심 코드**:
  ```java
  // 이메일 발송 - Gmail 우선, 실패 시 Naver 재시도
  public void sendWelcomeEmail(String toEmail, String userName) {
      SimpleMailMessage message = new SimpleMailMessage();
      message.setTo(toEmail);
      message.setSubject("[LearnIT] 회원가입을 환영합니다!");
      message.setText("회원가입이 완료되었습니다...");
      
      // Gmail로 먼저 시도
      try {
          message.setFrom("LearnIT <" + gmailFromEmail + ">");
          gmailMailSender.send(message);
          return;
      } catch (Exception e) {
          // Gmail 실패 시 Naver로 재시도
          message.setFrom("LearnIT <" + naverFromEmail + ">");
          naverMailSender.send(message);
      }
  }
  ```

### 5.2 마이페이지 기능

#### 5.2.1 대시보드 데이터 집계

  **문제점 → 해결책 (처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제: 다양한 데이터 소스의 효율적 집계 필요                            │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 강의, 학습 기록, 할일, 캘린더 등 다양한 데이터 소스
        │   → 단일 쿼리로 조회하기 어려움
        │   → 데이터 가공 및 병합 필요
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결: JOIN 쿼리 + Java Stream API를 활용한 데이터 집계                │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [대시보드 데이터 집계 프로세스]
        │       │
        │       ├─→ [1단계] 강의 데이터 JOIN 쿼리 조회
        │       │       │
        │       │       └─→ 학습 기록 집계
        │       │
        │       ├─→ [2단계] 할일 데이터 별도 조회
        │       │
        │       ├─→ [3단계] 캘린더 데이터 별도 조회
        │       │
        │       └─→ [4단계] Java Stream API로 데이터 가공
        │               │
        │               ├─→ 할일 + 캘린더 병합
        │               ├─→ 진행률 계산 (현재 강의 수 / 전체 강의 수)
        │               └─→ 통합 데이터 반환
        │
        ▼
  [완료] 대시보드 통합 데이터 반환
  ```

#### 5.2.2 프로필 관리 로직

  **문제점 → 해결책 (처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제 1: 소셜 로그인 사용자의 비밀번호 변경 시도                        │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 소셜 로그인 사용자는 비밀번호가 없음
        │   → 비밀번호 변경 시도 시 오류 발생 가능
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결 1: 사용자 타입별 분기 처리                                       │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [프로필 수정 프로세스]
        │       │
        │       ├─→ 사용자 타입 확인
        │       │       │
        │       │       ├─→ [소셜 로그인] → 비밀번호 변경 불가 처리
        │       │       │
        │       │       └─→ [일반 사용자]
        │       │               │
        │       │               └─→ 비밀번호 변경 시도
        │       │                       │
        │       │                       ├─→ 현재 비밀번호 BCrypt 검증
        │       │                       │       │
        │       │                       │       ├─→ [실패] → 에러 반환
        │       │                       │       │
        │       │                       │       └─→ [성공] → 새 비밀번호 BCrypt 암호화
        │       │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제 2: 프로필 이미지 저장 및 관리                                     │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 서버에 직접 저장 시 용량 부담
        │   → S3를 활용한 이미지 저장 필요
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결 2: S3 연동 및 프로필 정보 업데이트                                │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 프로필 정보 업데이트
        │       │
        │       ├─→ 이미지 업로드 확인
        │       │       │
        │       │       ├─→ [있음] → S3 업로드 → URL 저장
        │       │       │
        │       │       └─→ [없음] → 기존 이미지 유지
        │       │
        │       └─→ DB에 프로필 정보 저장
        │
        ▼
  [완료] 프로필 수정 완료
  ```

### 5.3 관리자 리뷰 관리 기능

#### 5.3.1 권한별 필터링 로직

  **문제점 → 해결책 (처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제: 관리자, 서브 어드민, 일반 사용자별 조회 권한 차이                │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 관리자: 모든 리뷰 조회 가능
        │   서브 어드민: 관리하는 강의의 리뷰만 조회
        │   일반 사용자: 접근 불가
        │   → 권한별로 다른 쿼리 필요
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결: 동적 SQL을 활용한 권한별 필터링                                 │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [리뷰 조회 프로세스]
        │       │
        │       ├─→ 사용자 권한 확인
        │       │       │
        │       │       ├─→ [ADMIN] → 전체 리뷰 조회
        │       │       │
        │       │       ├─→ [SUB_ADMIN]
        │       │       │       │
        │       │       │       ├─→ admin_user_role 테이블에서 관리 강의 ID 조회
        │       │       │       └─→ 동적 SQL 생성 (IN 절 필터링)
        │       │       │
        │       │       └─→ [일반 사용자] → 접근 불가
        │       │
        │       └─→ MyBatis 동적 쿼리 실행
        │               │
        │               └─→ 권한별 필터링된 리뷰 반환
        │
        ▼
  [완료] 권한별 필터링된 리뷰 반환
  ```

#### 5.3.2 검색 및 필터링

  **문제점 → 해결책 (처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제: 다양한 검색 조건과 상태 필터링의 효율적 처리                     │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 검색 타입: 강의명, 사용자명, 리뷰 내용
        │   상태 필터: Active, Approved, Rejected
        │   → 복잡한 WHERE 조건 조합 필요
        │   → 페이징과 함께 성능 최적화 필요
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결: 검색 타입별 분기 처리 및 동적 SQL 생성                           │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [리뷰 검색 프로세스]
        │       │
        │       ├─→ 검색 타입 확인
        │       │       │
        │       │       ├─→ [강의명] → 강의명 WHERE 조건 추가
        │       │       ├─→ [사용자명] → 사용자명 WHERE 조건 추가
        │       │       └─→ [리뷰 내용] → 리뷰 내용 WHERE 조건 추가
        │       │
        │       ├─→ 상태 필터 확인
        │       │       │
        │       │       ├─→ [Active] → STATUS = ACTIVE 조건 추가
        │       │       ├─→ [Approved] → STATUS = APPROVED 조건 추가
        │       │       ├─→ [Rejected] → STATUS = REJECTED 조건 추가
        │       │       └─→ [전체] → 상태 조건 없음
        │       │
        │       └─→ 페이징 처리 (LIMIT, OFFSET)
        │               │
        │               └─→ 필터링된 리뷰 반환
        │
        ▼
  [완료] 검색 및 필터링된 리뷰 반환
  ```

#### 5.3.3 리뷰 상태 관리

  **문제점 → 해결책 (처리 흐름)**
  ```
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 문제: 리뷰 상태 변경 및 삭제 시 데이터 복구 가능성                     │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ 하드 삭제 시 데이터 복구 불가
        │   → 상태 변경 이력 관리 필요
        │
        ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │ 해결: 소프트 삭제 및 상태 변경 이력 관리                               │
  └─────────────────────────────────────────────────────────────────────┘
        │
        ├─→ [리뷰 상태 변경 프로세스]
        │       │
        │       ├─→ 변경 타입 확인
        │       │       │
        │       │       ├─→ [승인] → STATUS = APPROVED 업데이트
        │       │       ├─→ [거부] → STATUS = REJECTED 업데이트
        │       │       └─→ [삭제] → 소프트 삭제 (DELETED = true)
        │       │
        │       ├─→ 상태 변경 이력 저장
        │       │
        │       └─→ DB 업데이트
        │               │
        │               ├─→ [성공] → 상태 변경 완료
        │               │
        │               └─→ [실패] → 롤백 및 에러 반환
        │
        ▼
  [완료] 리뷰 상태 변경 완료 (데이터 복구 가능)
  ```

---

## 06. 주요 화면

### 회원/인증 관련 화면 (스크린샷 추가 필요)
- **로그인 화면**: 일반 로그인 및 소셜 로그인 버튼
- **회원가입 화면**: 이메일 중복 검증, 비밀번호 강도 표시
- **비밀번호 찾기 화면**: 이메일 입력 및 임시 비밀번호 발송
- **소셜 회원가입 추가 정보 입력 화면**: GitHub URL 자동 포맷팅 기능

### 마이페이지 화면 (스크린샷 추가 필요)
- **대시보드**: 학습 진행률, 강의 목록, 할일 관리, 캘린더 통합
- **프로필 관리**: 프로필 이미지 업로드, 개인정보 수정, 비밀번호 변경

### 관리자 리뷰 관리 화면 (스크린샷 추가 필요)
- **리뷰 목록**: 검색, 필터링, 페이징 처리
- **리뷰 상세**: 승인/거부/삭제 기능, 상태 변경 이력

### UI/UX 특징
- 반응형 디자인으로 모바일/데스크톱 대응
- AJAX를 통한 비동기 데이터 로딩으로 사용자 경험 향상
- 직관적인 네비게이션 및 정보 구조화

---

## 07. 트러블 슈팅

### 7.1 인증/인가 이슈

**구글 OAuth 'sub' 속성 null 예외**
- **문제**: 구글 OAuth 로그인 시 `sub` 속성이 null인 경우 `IllegalArgumentException` 발생
- **원인**: Spring Security OAuth2의 기본 설정이 `user-name-attribute`를 `sub`로 설정했으나, 일부 구글 계정에서는 `sub` 속성이 제공되지 않음
- **해결**: 예외 처리 로직 추가 및 직접 API 호출 방식으로 대체하여 사용자 정보 획득

**소셜 로그인 사용자 비밀번호 변경 방지**
- **문제**: 소셜 로그인으로 가입한 사용자가 비밀번호 변경을 시도하는 경우 처리 필요
- **해결**: 사용자 엔티티의 `provider` 필드를 확인하여 소셜 로그인 여부 판단, 소셜 로그인 사용자의 경우 비밀번호 변경 요청 시 예외 발생

### 7.2 데이터 정합성 문제

**게스트 장바구니 병합**
- **문제**: 게스트 사용자가 장바구니에 담은 상품이 로그인 후 사라지는 문제
- **해결**: 로그인 성공 핸들러에서 게스트 장바구니와 로그인 사용자 장바구니를 자동 병합하는 로직 구현

### 7.3 상태 관리 및 성능 문제

**서브 어드민 권한 필터링 성능 이슈**
- **문제**: 서브 어드민이 관리하는 강의가 많을 경우 IN 절의 성능 저하
- **해결**: 관리하는 강의가 없는 경우 전체 권한으로 처리, 인덱스 최적화 및 쿼리 실행 계획 분석

**대시보드 데이터 로딩 성능**
- **문제**: 대시보드 초기 로딩 시 여러 데이터 소스를 조회하여 느린 응답 시간
- **해결**: AJAX를 통한 비동기 데이터 로딩, 필요한 데이터만 우선 로딩하고 나머지는 지연 로딩

---

## 08. 성과 및 배운 점

### 교육 분야 관심 및 실무 경험

**온라인 교육 플랫폼 개발 경험**
- IT 온라인 교육의 핵심 문제점(학습 흐름 단절, 협업 기능 부재)을 직접 파악하고 해결 방안 설계
- 학습자 경험을 고려한 기능 설계 및 구현 (대시보드, 학습 진행률 추적, 할일 관리)
- 교육 콘텐츠 제공 플랫폼의 전체 아키텍처 이해 및 구현

**데이터 사이언스 실무 경험**
- **대시보드 데이터 집계**: 다양한 데이터 소스(강의, 학습 기록, 할일, 캘린더)를 효율적으로 집계
- **데이터 가공 및 분석**: Java Stream API를 활용한 복잡한 데이터 변환 및 집계 로직 구현
- **진행률 계산 알고리즘**: 현재 강의 수 / 전체 강의 수 기반 학습 진행률 산출 로직 설계
- **성능 최적화**: AJAX를 통한 비동기 데이터 로딩으로 대용량 데이터 처리 최적화

### 프로그래밍 역량 및 Computer Science 기초

**자료 구조 및 알고리즘 활용**
- **동적 쿼리 최적화**: MyBatis의 `<if>` 태그를 활용한 조건부 SQL 생성으로 O(n) 복잡도 최적화
- **데이터 병합 알고리즘**: 캘린더 데이터와 할일 데이터를 별도 조회 후 Java에서 효율적으로 병합
- **필터링 알고리즘**: 권한별 데이터 필터링을 위한 동적 IN 절 생성 및 최적화
- **트랜잭션 관리**: 이메일 발송 실패 시 롤백 처리 등 ACID 원칙 준수

**Best Practices를 따르는 깔끔한 코드**
- **레이어 분리**: Controller-Service-Repository 계층 구조로 관심사 분리
- **예외 처리**: Provider별 OAuth 응답 구조 차이를 예외 처리로 안전하게 처리
- **코드 재사용성**: 공통 로직 추출 및 DTO 패턴 활용으로 유지보수성 향상
- **보안 Best Practices**: BCrypt 암호화, 세션 기반 인증, Open Redirect 방지, 권한별 접근 제어

### 기술 스택 실무 역량

**Backend (Java, Spring)**
- Java 17, Spring Boot 3.x 기반 RESTful API 개발
- Spring Security를 활용한 인증/인가 시스템 구축
- OAuth2 Client를 통한 소셜 로그인 통합 (카카오, 구글)
- MyBatis를 활용한 복잡한 동적 쿼리 작성 및 최적화

**Frontend (JavaScript, HTML, CSS)**
- jQuery, Ajax를 활용한 비동기 데이터 통신 구현
- 사용자 경험을 고려한 UI/UX 개발
- AJAX를 통한 지연 로딩으로 성능 최적화

**Database & Infra (SQL, AWS)**
- MySQL을 활용한 복잡한 JOIN 쿼리 작성 및 인덱스 최적화
- AWS (EC2, S3, RDS) 환경에서의 배포 및 운영 경험
- Docker, Docker Compose를 활용한 컨테이너화
- Nginx를 통한 리버스 프록시 설정

### 디자인 감각 및 사용자 경험

**UI/UX 개발 경험**
- 담당 기능의 화면 구현 및 사용자 인터페이스 설계
- 대시보드 데이터 시각화를 통한 정보 구조화
- 비동기 데이터 로딩을 통한 사용자 경험 최적화
- 반응형 디자인 고려 및 모바일 환경 대응

### 설계 관점의 개선 인식

**확장 가능한 구조 설계**
- 공통 로직 추출 및 재사용성 향상
- 페이징 처리 표준화로 유지보수성 개선
- 동적 쿼리를 통한 유연한 필터링 시스템
- Provider별 분기 처리로 새로운 OAuth Provider 추가 용이

**보안 강화 인식**
- Open Redirect 방지 (리다이렉트 URL 화이트리스트 검증)
- 세션 기반 인증 관리
- 권한별 데이터 접근 제어
- BCrypt를 통한 비밀번호 암호화
- 이메일 발송 실패 시 롤백 처리로 트랜잭션 안전성 보장

**성능 최적화 고려**
- 쿼리 최적화 및 인덱스 활용
- 비동기 데이터 로딩 (AJAX)
- 페이징 처리로 대용량 데이터 효율적 처리
- 서브 어드민 권한 필터링 성능 이슈 해결 (IN 절 최적화)

### 협업 경험

- **Git 브랜치 전략**: 기능별 브랜치 분리 및 PR을 통한 코드 리뷰
- **코드 컨벤션**: 팀 내 코딩 스타일 통일 및 일관성 유지
- **문서화**: API 문서 및 기능 명세서 작성
- **트러블 슈팅**: 문제 해결 과정 문서화 및 팀 내 공유

### 개선 사항 및 향후 계획

1. **보안 강화**
   - JWT 토큰 기반 인증으로 전환 검토
   - CSRF 토큰 적용

2. **성능 최적화**
   - 대시보드 데이터 캐싱 적용
   - 페이징 쿼리 최적화

3. **테스트 코드 작성**
   - 단위 테스트 및 통합 테스트 추가
   - 테스트 커버리지 향상

---

## 📎 첨부 자료

### 필수 첨부 자료 (추가 권장)

1. **시스템 아키텍처 다이어그램**
   - 전체 시스템 구조도 (클라이언트 → 서버 → DB)
   - 컴포넌트 간 상호작용 흐름도
   - 배포 아키텍처 (AWS 인프라 구성)

2. **데이터베이스 ERD (Entity Relationship Diagram)**
   - 주요 엔티티 및 관계도
   - 테이블 간 외래키 관계 시각화
   - 도구: MySQL Workbench, ERD Cloud, draw.io 등

3. **주요 테이블 스키마 스크린샷**
   - User 테이블 구조
   - Review 테이블 구조
   - admin_user_role 테이블 구조
   - 인덱스 정보 포함

4. **주요 화면 스크린샷**
   - 로그인/회원가입 화면
   - 대시보드 화면 (데이터 시각화)
   - 관리자 리뷰 관리 화면
   - 프로필 관리 화면

5. **API 명세서** (선택)
   - RESTful API 엔드포인트 목록
   - 요청/응답 예시
   - Swagger/Postman 문서

### 추가 권장 자료

6. **코드 품질 증명**
   - 주요 클래스 구조 (패키지 구조)
   - 코드 리뷰 결과 (PR 스크린샷)
   - 테스트 커버리지 리포트 (있는 경우)

7. **성능 최적화 증명**
   - 쿼리 실행 계획 (EXPLAIN 결과)
   - 인덱스 최적화 전/후 비교
   - AJAX 비동기 로딩 전/후 성능 비교

8. **Git 커밋 히스토리** (선택)
   - 주요 기능별 커밋 로그
   - 브랜치 전략 시각화

---

# 점글이 수능 학습 프로젝트

<span style="background-color: #0ea5e9; color: white; padding: 4px 12px; border-radius: 4px; font-weight: bold; font-size: 0.85em;">PROJECT</span> **점글이 수능 학습** (Jeomgeuli Suneung Learning)

**Project Period**  
2025.09 - 2025.12 (12주) / 1명(개인 프로젝트)

**Project Role**  
기획, 설계, 개발, 배포 전 과정 담당

---

## [SERVICE OVERVIEW]

점글이 수능 학습은 시각장애인을 위한 AI 기반 수능 학습 지원 플랫폼입니다. 시각장애인용 점자 교재는 일반 수험생 대비 2~6개월 늦게 제공되는 구조적 문제가 있죠. 본 서비스는 AI 기반 자동화 시스템을 통해 교재를 자동으로 변환하여, 일반 수험생과 동등한 시점에 학습 자료에 접근할 수 있도록 도와줍니다. 교재를 업로드하면 자동으로 구조화되고, 점자 디스플레이로 읽거나 AI 학습 도우미에게 실시간으로 질문할 수 있죠.

---

## [WHAT I LEARNED]

시각장애인을 위한 서비스를 만들기 위해 접근성과 사용자 경험을 동시에 고려하는 설계를 많이 고민했고, PDF 파싱부터 점자 변환, 하드웨어 연동까지 다양한 기술을 통합해야 하는 만큼 백엔드 아키텍처 설계 과정이 무척 즐거웠습니다. 처음 접해보는 기술들을 통합하는 과정에서 많은 것을 배울 수 있었고, 사용자 조사부터 배포까지 전 과정을 혼자 담당한 첫 풀스택 프로젝트라는 점에서 의미가 있습니다.

---

**작성일**: 2026.01.26  
**작성자**: [본인 이름]
