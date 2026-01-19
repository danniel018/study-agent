# Database Entity Relationship Diagram

## ERD Diagram

```mermaid
erDiagram
    users {
        int id PK
        bigint telegram_id UK
        string username
        string first_name
        string last_name
        string timezone
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    repositories {
        int id PK
        int user_id FK
        string repo_url
        string repo_owner
        string repo_name
        boolean is_active
        datetime created_at
        datetime last_synced_at
    }
    
    topics {
        int id PK
        int repository_id FK
        string title
        json file_paths
        text content
        string content_hash
        datetime last_synced_at
    }
    
    study_sessions {
        int id PK
        int user_id FK
        int topic_id FK
        string session_type
        datetime started_at
        datetime completed_at
        string status
    }
    
    assessments {
        int id PK
        int session_id FK
        text question
        text user_answer
        text correct_answer
        boolean is_correct
        text llm_feedback
        float score
        datetime answered_at
    }
    
    performance_metrics {
        int id PK
        int user_id FK
        int topic_id FK
        int total_sessions
        int total_correct
        int total_questions
        float average_score
        datetime last_studied_at
        datetime next_review_at
        float retention_score
        datetime created_at
        datetime updated_at
    }
    
    schedule_config {
        int id PK
        int user_id FK,UK
        boolean is_enabled
        string frequency
        string preferred_time
        string days_of_week
        int questions_per_session
    }
    
    users ||--o{ repositories : "has"
    users ||--o{ study_sessions : "participates in"
    users ||--o{ performance_metrics : "tracks"
    users ||--o| schedule_config : "configures"
    
    repositories ||--o{ topics : "contains"
    
    topics ||--o{ study_sessions : "studied in"
    topics ||--o{ performance_metrics : "measured by"
    
    study_sessions ||--o{ assessments : "contains"
```

## Table Descriptions

| Entity | Description |
|--------|-------------|
| **users** | Stores Telegram user information with timezone preferences |
| **repositories** | GitHub repositories linked to users (unique per user+owner+name) |
| **topics** | Study topics extracted from repository content |
| **study_sessions** | Tracks individual study sessions (scheduled/manual) |
| **assessments** | Questions and answers within a study session |
| **performance_metrics** | Aggregated performance data per user+topic (unique constraint) |
| **schedule_config** | User's scheduling preferences (one-to-one with user) |

## Relationships

- **User → Repositories**: One-to-many (user owns multiple repos)
- **User → Study Sessions**: One-to-many (user has multiple sessions)
- **User → Performance Metrics**: One-to-many (metrics per topic)
- **User → Schedule Config**: One-to-one (single config per user)
- **Repository → Topics**: One-to-many (repo contains multiple topics)
- **Topic → Study Sessions**: One-to-many (topic studied multiple times)
- **Topic → Performance Metrics**: One-to-many (tracked per user)
- **Study Session → Assessments**: One-to-many (session has multiple Q&A)
