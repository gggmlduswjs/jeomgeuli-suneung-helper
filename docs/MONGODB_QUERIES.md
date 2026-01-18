# MongoDB 쿼리 예시

## 기본 조회 패턴

### 1. 레슨 전체 조회 (가장 빈번한 쿼리)

```javascript
// 레슨 ID로 전체 레슨 조회
db.lessons.findOne({ lessonId: "korean_01" })

// 결과: 레슨 메타데이터 + 모든 블록 포함
```

**설계 이유**: 사용자는 항상 "하나의 레슨"을 조회하므로, 블록을 별도로 조회할 필요 없음

---

### 2. 특정 블록 조회

```javascript
// 레슨 내 특정 블록 찾기
db.lessons.findOne(
  { lessonId: "korean_01" },
  { 
    blocks: { 
      $elemMatch: { blockId: "korean_01_b005" } 
    } 
  }
)
```

**설계 이유**: 북마크나 복습 시 특정 블록만 필요할 때 사용

---

### 3. 과목별 레슨 목록 조회

```javascript
// 문학 과목의 모든 레슨 목록
db.lessons.find(
  { subject: "korean" },
  { 
    lessonId: 1, 
    title: 1, 
    order: 1,
    "metadata.estimatedDuration": 1
  }
).sort({ order: 1 })
```

**설계 이유**: 레슨 선택 화면에서 사용

---

### 4. 사용자 진행 상태 업데이트

```javascript
// 현재 블록 업데이트
db.lessons.updateOne(
  { lessonId: "korean_01" },
  { 
    $set: { 
      "progress.currentBlock": "korean_01_b005",
      "progress.lastAccessed": new Date()
    },
    $addToSet: {
      "progress.completedBlocks": "korean_01_b004"
    }
  }
)
```

**설계 이유**: 사용자가 블록을 완료할 때마다 진행 상태 저장

---

### 5. 북마크 추가/제거

```javascript
// 북마크 추가
db.lessons.updateOne(
  { lessonId: "korean_01" },
  { 
    $addToSet: { 
      "progress.bookmarks": "korean_01_b004"
    }
  }
)

// 북마크 제거
db.lessons.updateOne(
  { lessonId: "korean_01" },
  { 
    $pull: { 
      "progress.bookmarks": "korean_01_b004"
    }
  }
)
```

---

### 6. 블록 타입별 필터링

```javascript
// 문제 적용 블록만 조회
db.lessons.aggregate([
  { $match: { lessonId: "korean_01" } },
  { $unwind: "$blocks" },
  { $match: { "blocks.type": "problem_application" } },
  { $project: { blocks: 1 } }
])
```

**설계 이유**: 문제만 따로 복습하고 싶을 때

---

### 7. 다음 블록 찾기

```javascript
// 현재 블록의 다음 블록 찾기
db.lessons.aggregate([
  { $match: { lessonId: "korean_01" } },
  { $unwind: { path: "$blocks", includeArrayIndex: "index" } },
  { $match: { "blocks.blockId": "korean_01_b004" } },
  { $lookup: {
      from: "lessons",
      let: { lessonId: "$lessonId", nextIndex: { $add: ["$index", 1] } },
      pipeline: [
        { $match: { $expr: { $eq: ["$lessonId", "$$lessonId"] } } },
        { $unwind: { path: "$blocks", includeArrayIndex: "idx" } },
        { $match: { $expr: { $eq: ["$idx", "$$nextIndex"] } } },
        { $project: { blocks: 1 } }
      ],
      as: "nextBlock"
    }
  }
])
```

**더 간단한 방법**: 애플리케이션 레벨에서 처리
```python
# Python 예시
lesson = db.lessons.find_one({"lessonId": "korean_01"})
current_block_index = next(
    i for i, block in enumerate(lesson['blocks']) 
    if block['blockId'] == "korean_01_b004"
)
next_block = lesson['blocks'][current_block_index + 1]
```

**설계 이유**: 레슨 전체를 이미 메모리에 로드했으므로, 애플리케이션 레벨에서 처리하는 것이 더 효율적

---

## 인덱스 설계

```javascript
// 레슨 ID로 빠른 조회
db.lessons.createIndex({ lessonId: 1 }, { unique: true })

// 과목별 조회 최적화
db.lessons.createIndex({ subject: 1, order: 1 })

// 사용자 진행 상태 조회
db.lessons.createIndex({ "progress.userId": 1, "progress.lastAccessed": -1 })

// 블록 ID로 빠른 검색 (필요한 경우)
db.lessons.createIndex({ "blocks.blockId": 1 })
```

---

## 데이터 마이그레이션 예시

### 기존 JSON 데이터를 MongoDB 형식으로 변환

```python
# 기존 parsed/literature/korean_01.json을 MongoDB 형식으로 변환
def convert_lesson_json_to_mongodb(json_data: dict) -> dict:
    """기존 JSON 구조를 MongoDB 레슨 문서로 변환"""
    
    blocks = []
    for section in json_data.get('sections', []):
        for unit in section.get('units', []):
            # Unit을 Block으로 변환
            block = {
                "blockId": unit['unitId'],
                "type": _map_unit_type_to_block_type(unit['type']),
                "order": len(blocks) + 1,
                "learningIntent": {
                    "title": section.get('title', ''),
                    "description": _extract_description(unit)
                },
                "brailleSignal": _get_braille_signal(unit['type']),
                "audioRange": {
                    "start": "00:00:00",  # 실제 타임스탬프 필요
                    "end": "00:00:00"
                },
                "userAwareness": {
                    "message": _get_awareness_message(unit['type']),
                    "context": section.get('title', '')
                },
                "uiBehavior": {
                    "autoPlay": unit['type'] != 'problem_intro',
                    "bookmarkable": True,
                    "reviewable": True
                },
                "content": {
                    "script": unit.get('content', '')
                }
            }
            blocks.append(block)
    
    return {
        "lessonId": json_data['lessonId'],
        "subject": json_data['subject'],
        "title": json_data['title'],
        "order": json_data['order'],
        "metadata": {
            "year": 2026,
            "curriculum": "수능특강",
            "estimatedDuration": 3600,  # 실제 계산 필요
            "difficulty": "basic"
        },
        "blocks": blocks,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow()
    }
```
