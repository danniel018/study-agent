# Study Agent - Questions and Clarifications

## Purpose

This document outlines questions and areas that need clarification before proceeding with full implementation. These questions will help ensure the system meets user expectations and business requirements.

---

## 1. GitHub Repository Access & Content Discovery

### Question 1.1: Repository Structure
**Q**: What is the expected structure of study materials in GitHub repositories?

**Options**:
- A) Any `.md` files are considered study topics
- B) Only files in a specific directory (e.g., `/notes/`, `/topics/`)
- C) Files must follow a naming convention (e.g., `topic-*.md`)
- D) Configuration file (e.g., `.study-agent.yml`) defines which files to include

**Recommendation**: Option D (configuration file) provides the most flexibility. Example:
```yaml
# .study-agent.yml
topics:
  - path: "notes/*.md"
  - path: "lectures/week-*.md"
exclude:
  - "README.md"
  - "drafts/*.md"
```

### Question 1.2: Private Repository Support
**Q**: Should the system support private GitHub repositories?

**Considerations**:
- Requires GitHub Personal Access Token (PAT) or OAuth
- Security implications of storing tokens
- User must grant repository access

**Options**:
- A) MVP: Public repositories only
- B) MVP: Support private repos with user-provided PAT
- C) MVP: Support private repos with OAuth flow

**Recommendation**: Start with **Option A** (public only), add PAT support in Phase 2.

### Question 1.3: Content Parsing
**Q**: How should the system extract topics from markdown files?

**Options**:
- A) Each file = one topic
- B) Each H1 heading = one topic
- C) Each H2 heading = one topic  
- D) Configurable (H1, H2, or file-level)

**Example** of Option C (H2 headings):
```markdown
# Python Programming

## Variables and Data Types
Content about variables...

## Control Flow
Content about control flow...
```
This would create 2 topics: "Variables and Data Types" and "Control Flow"

**Recommendation**: **Option D** with default of H2 headings.

---

## 2. Quiz Generation & Assessment

### Question 2.1: Quiz Question Types
**Q**: What types of quiz questions should be supported?

**Options**:
- A) Multiple choice only
- B) True/False only
- C) Open-ended only (free text)
- D) Mix of multiple choice and open-ended
- E) Multiple choice, True/False, Fill-in-the-blank, Open-ended

**Recommendation**: **Option D** for MVP (multiple choice + open-ended), expand to E later.

### Question 2.2: Difficulty Levels
**Q**: Should the system support different difficulty levels?

**Options**:
- A) No difficulty levels (uniform difficulty)
- B) Yes, fixed difficulty per user (easy/medium/hard)
- C) Yes, adaptive difficulty based on performance
- D) Yes, difficulty per topic based on mastery level

**Recommendation**: **Option B** for MVP, **Option C** for Phase 2.

### Question 2.3: Number of Questions
**Q**: How many questions per study session?

**Options**:
- A) Fixed number (e.g., 5 questions)
- B) User-configurable (3-10 questions)
- C) Adaptive based on topic complexity
- D) Time-based (as many as fit in X minutes)

**Recommendation**: **Option B** with default of 5 questions.

### Question 2.4: Answer Evaluation
**Q**: How should open-ended answers be evaluated?

**Approach**:
- Use LLM (Gemini) to evaluate semantic correctness
- Provide partial credit (0.0 to 1.0 score)
- Generate feedback for incorrect/incomplete answers

**Clarifications Needed**:
- Should the system be strict or lenient?
- Accept answers that are correct but differently worded?
- How much weight for partial credit?

**Recommendation**: Use LLM for semantic evaluation with partial credit. Accept answers that demonstrate understanding even if wording differs.

---

## 3. Scheduling & Spaced Repetition

### Question 3.1: Scheduling Algorithm
**Q**: What algorithm should determine when to review topics?

**Options**:
- A) Fixed schedule (e.g., every 3 days)
- B) Simple spaced repetition (e.g., 1 day, 3 days, 7 days, 14 days)
- C) SM-2 algorithm (SuperMemo 2)
- D) Custom algorithm based on performance

**Recommendation**: **Option B** for MVP (simple spaced repetition), **Option C** for Phase 2.

**Example Simple Algorithm**:
```python
def calculate_next_review(score: float, last_interval: int) -> int:
    """
    Calculate next review interval in days.
    
    Args:
        score: Quiz score (0.0 to 1.0)
        last_interval: Previous interval in days
        
    Returns:
        Next interval in days
    """
    if score >= 0.8:
        # Good performance: increase interval
        return int(last_interval * 2.5)
    elif score >= 0.6:
        # Okay performance: slight increase
        return int(last_interval * 1.5)
    else:
        # Poor performance: reset to 1 day
        return 1
```

### Question 3.2: Default Schedule
**Q**: What should be the default assessment schedule?

**Options**:
- A) Daily at a fixed time (e.g., 9 AM)
- B) User chooses time during onboarding
- C) Adaptive based on user activity patterns
- D) No default schedule (user must configure)

**Recommendation**: **Option B** - ask during onboarding, default to 9 AM user's timezone.

### Question 3.3: Missed Assessments
**Q**: How should the system handle missed scheduled assessments?

**Options**:
- A) Skip missed assessments, wait for next scheduled time
- B) Accumulate missed assessments (backlog)
- C) Send reminders and reschedule
- D) Adjust schedule based on user availability

**Recommendation**: **Option C** for user engagement - send one reminder, then reschedule if still missed.

---

## 4. User Experience & Interface

### Question 4.1: Onboarding Flow
**Q**: What information should be collected during user onboarding?

**Suggested Flow**:
1. Welcome message
2. Request timezone
3. Request preferred study time
4. Request first GitHub repository URL
5. Confirm topics found
6. Configure initial schedule

**Question**: Is this flow appropriate? Any additional steps?

### Question 4.2: Notification Preferences
**Q**: Should users be able to configure notification preferences?

**Options**:
- A) All notifications enabled by default (non-configurable)
- B) Users can enable/disable specific notification types
- C) Users can set "Do Not Disturb" hours
- D) Both B and C

**Notification Types**:
- Scheduled assessment reminders
- Study streak notifications
- Performance milestones
- New topics added

**Recommendation**: **Option D** for better user control.

### Question 4.3: Study Session Length
**Q**: Should there be a time limit for study sessions?

**Options**:
- A) No time limit
- B) Soft limit (reminder after X minutes)
- C) Hard limit (session expires after X minutes)

**Recommendation**: **Option B** with 15-minute soft limit to encourage completion without forcing it.

### Question 4.4: Multi-Repository Support
**Q**: Should users be able to study from multiple repositories simultaneously?

**Considerations**:
- Separate topics from different repos
- Combined quiz from all repos
- Schedule per repo vs. global schedule

**Options**:
- A) Single repository only
- B) Multiple repositories, combined into one topic pool
- C) Multiple repositories, separate tracking per repo
- D) Multiple repositories, user chooses which to include in session

**Recommendation**: **Option D** for maximum flexibility.

---

## 5. Performance Tracking & Analytics

### Question 5.1: Metrics to Track
**Q**: What performance metrics should be displayed to users?

**Suggested Metrics**:
- Overall accuracy (% correct)
- Topics mastered / in progress / need review
- Study streak (consecutive days)
- Total study time
- Questions answered
- Average score per topic
- Improvement over time (weekly/monthly trends)

**Question**: Are these metrics sufficient? Any additions?

### Question 5.2: Goal Setting
**Q**: Should the system support user-defined goals?

**Examples**:
- "Study 30 minutes per day"
- "Complete 5 sessions per week"
- "Achieve 80% accuracy on all topics"
- "Master 10 topics this month"

**Options**:
- A) No goal setting
- B) Predefined goals only
- C) Custom user-defined goals
- D) Both predefined and custom goals

**Recommendation**: **Option D** - helps with motivation and engagement.

### Question 5.3: Progress Visualization
**Q**: How should progress be visualized in the chat?

**Options**:
- A) Text-only (e.g., "Score: 8/10 (80%)")
- B) Text with emoji bars (e.g., "Progress: ⬛⬛⬛⬛⬛⬜⬜⬜⬜⬜ 50%")
- C) Generated charts sent as images
- D) Link to web dashboard

**Recommendation**: **Option B** for MVP (works well in chat), **Option C** for Phase 2.

---

## 6. Content Management

### Question 6.1: Content Updates
**Q**: How often should the system sync GitHub repositories?

**Options**:
- A) Manual sync only (user triggers)
- B) Scheduled sync (e.g., daily)
- C) Webhook-based (GitHub notifies on changes)
- D) Hybrid (scheduled + manual)

**Recommendation**: **Option D** - daily auto-sync + manual trigger option.

### Question 6.2: Content Changes Impact
**Q**: How should the system handle updated content?

**Scenarios**:
1. Topic content is updated
2. Topic is deleted
3. New topics are added

**Options**:
- A) Reset performance metrics for changed topics
- B) Maintain metrics but flag content as updated
- C) Keep metrics unchanged
- D) User chooses on first sync

**Recommendation**: **Option B** - preserve history but notify user of changes.

### Question 6.3: Duplicate Content
**Q**: How to handle topics with similar content across repositories?

**Options**:
- A) Keep all duplicates as separate topics
- B) Detect and merge similar topics
- C) Allow user to link related topics
- D) Show warning but allow duplicates

**Recommendation**: **Option D** for MVP (simpler), **Option C** for Phase 2.

---

## 7. LLM Configuration

### Question 7.1: Gemini Model Selection
**Q**: Which Gemini model should be used?

**Options**:
- A) `gemini-pro` (text-only, faster, cheaper)
- B) `gemini-pro-vision` (supports images in study materials)
- C) `gemini-1.5-pro` (latest, more capable)
- D) Configurable per use case

**Recommendation**: **Option A** for MVP, **Option D** for Phase 2 when adding image support.

### Question 7.2: Prompt Engineering
**Q**: How much context should be provided to the LLM?

**For Quiz Generation**:
- Just the topic content?
- Topic + related topics?
- Topic + user's performance history?

**For Answer Evaluation**:
- Question + user answer + correct answer?
- Add topic context for semantic understanding?

**Recommendation**: 
- **Quiz Gen**: Topic content + difficulty level
- **Evaluation**: Question + user answer + topic context (for semantic understanding)

### Question 7.3: Fallback Handling
**Q**: What happens if Gemini API fails or rate limits are hit?

**Options**:
- A) Show error and skip session
- B) Use cached questions from previous sessions
- C) Retry with exponential backoff
- D) Queue for later processing

**Recommendation**: **Option C** with fallback to **Option B** if still failing.

---

## 8. Data Privacy & Security

### Question 8.1: Data Retention
**Q**: How long should user data be retained?

**Data Types**:
- User profile
- Study sessions
- Performance metrics
- Quiz questions and answers

**Options**:
- A) Indefinitely (until user deletes account)
- B) Fixed period (e.g., 1 year)
- C) Configurable per user
- D) Different retention for different data types

**Recommendation**: **Option A** for core data, with export/delete options.

### Question 8.2: Data Export
**Q**: Should users be able to export their data?

**Format Options**:
- JSON
- CSV
- PDF report

**Recommendation**: Yes, provide JSON export for all user data (GDPR compliance).

### Question 8.3: Repository Content Storage
**Q**: How long should fetched GitHub content be cached?

**Considerations**:
- Reduces API calls
- May become stale
- Storage costs

**Options**:
- A) Cache indefinitely (until manual sync)
- B) Cache for 24 hours
- C) Cache for 7 days
- D) Configurable TTL

**Recommendation**: **Option C** - 7-day cache with daily sync check.

---

## 9. Error Handling & Edge Cases

### Question 9.1: Invalid Repository Handling
**Q**: What if a GitHub repository URL is invalid or inaccessible?

**Scenarios**:
- Repository doesn't exist
- Repository is private (no access)
- Repository has no markdown files
- Repository is archived/deleted

**Recommendation**: 
- Validate URL format
- Check repository accessibility
- Show clear error messages
- Suggest fixes

### Question 9.2: Empty or Poor Content
**Q**: What if topic content is too short or low quality?

**Examples**:
- Only 1-2 sentences
- Just code snippets, no explanations
- Unintelligible content

**Options**:
- A) Skip topics below minimum length threshold
- B) Generate questions anyway
- C) Warn user and ask to improve content
- D) Combine short topics

**Recommendation**: **Option A** - require minimum 100 words per topic, show warning for skipped topics.

### Question 9.3: LLM Generated Bad Questions
**Q**: What if LLM generates poor quality questions?

**Options**:
- A) User can report bad questions
- B) Automatic quality check (detect nonsensical questions)
- C) User can skip questions
- D) All of the above

**Recommendation**: **Option D** - multi-layer quality assurance.

---

## 10. Testing & Quality Assurance

### Question 10.1: Test Data
**Q**: Should we create sample repositories for testing?

**Suggestion**: Yes, create public test repositories with:
- Computer Science fundamentals
- Python programming
- Data structures
- Algorithms

**Question**: What other topics would be useful for testing?

### Question 10.2: Coverage Requirements
**Q**: Is 90% code coverage realistic for MVP?

**Considerations**:
- High quality assurance
- More development time
- May be challenging for UI code

**Options**:
- A) Maintain 90% target
- B) Lower to 80% for MVP
- C) Different targets per layer (80% domain, 70% presentation)

**Recommendation**: **Option C** - flexible but still high quality.

### Question 10.3: Performance Testing
**Q**: What performance benchmarks should be met?

**Suggested Metrics**:
- Repository sync: < 30 seconds for typical repo
- Quiz generation: < 5 seconds
- Answer evaluation: < 3 seconds
- Bot response time: < 1 second

**Question**: Are these targets appropriate?

---

## 11. Deployment & Operations

### Question 11.1: Hosting Environment
**Q**: What is the target deployment environment?

**Options**:
- A) Self-hosted (VPS)
- B) Cloud platform (AWS, GCP, Azure)
- C) Serverless (AWS Lambda, Google Cloud Functions)
- D) Container platform (Docker + Kubernetes)
- E) PaaS (Heroku, Railway, Render)

**Question**: What's your preference and existing infrastructure?

### Question 11.2: Database Scaling
**Q**: When should we consider migrating from SQLite?

**Triggers**:
- X concurrent users
- Y GB of data
- Performance degradation

**Recommendation**: Plan migration to PostgreSQL when:
- \> 100 active users
- \> 1GB database size
- Concurrent access issues

### Question 11.3: Monitoring
**Q**: What monitoring/observability tools should be integrated?

**Options**:
- A) Basic logging only
- B) Application Performance Monitoring (APM)
- C) Error tracking (Sentry)
- D) All of the above

**Recommendation**: **Option D** for production readiness.

---

## 12. Future Enhancements

### Question 12.1: Priority Features
**Q**: After MVP, what features should be prioritized?

**Suggestions** (in priority order):
1. Advanced spaced repetition (SM-2)
2. Private repository support
3. WhatsApp integration
4. Team/group study features
5. Integration with note-taking apps
6. Mobile app
7. Gamification (badges, leaderboards)
8. Voice interaction

**Question**: What's your priority order?

### Question 12.2: Monetization
**Q**: Is this a free/open-source project or will it have paid tiers?

**Options**:
- A) Fully free and open-source
- B) Free tier + paid premium features
- C) One-time purchase
- D) Subscription model

**Question**: What's the intended business model?

### Question 12.3: Community Features
**Q**: Should users be able to share topics or quiz questions?

**Options**:
- A) Private use only
- B) Share topics with specific users
- C) Public topic library
- D) Community-curated questions

**Recommendation**: Start with **Option A**, consider **Option C** for Phase 3.

---

## Summary of Key Questions Requiring Immediate Answers

### Critical for MVP Implementation:

1. **Repository Structure**: How to identify study topics in repos? (Question 1.1)
2. **Question Types**: Multiple choice, open-ended, or both? (Question 2.1)
3. **Scheduling Algorithm**: Simple vs. advanced spaced repetition? (Question 3.1)
4. **Default Schedule**: What time should assessments default to? (Question 3.2)
5. **Multi-Repository**: Support multiple repos from start? (Question 4.4)
6. **Deployment Target**: Where will this be hosted? (Question 11.1)

### Important but Can Be Decided During Development:

7. **Difficulty Levels**: Fixed vs. adaptive? (Question 2.2)
8. **Content Sync**: How often? (Question 6.1)
9. **Gemini Model**: Which version? (Question 7.1)
10. **Test Coverage**: 90% or flexible? (Question 10.2)

### Can Be Deferred to Post-MVP:

11. **Private Repos**: Required for MVP? (Question 1.2)
12. **Goal Setting**: Include in MVP? (Question 5.2)
13. **Data Export**: Required for MVP? (Question 8.2)
14. **Monetization**: What's the plan? (Question 12.2)

---

## Next Steps

1. **Review Questions**: Go through critical questions (1-6)
2. **Provide Answers**: Answer or clarify each question
3. **Update Design**: Refine design based on answers
4. **Begin Implementation**: Start with core architecture
5. **Iterative Review**: Address remaining questions during development

Please provide answers to the critical questions so we can finalize the design and begin implementation!
