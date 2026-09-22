---
feature: subject-scoped-bank
stories: 4
acceptance_criteria: 9
---

# Requirements — Question bank filtered by subject first

## US-01 — Subject tabs
**Priority:** must

**AC-01** — One subject at a time
```gherkin
Given an org with Toán and Vật lý questions
When I open the bank
Then I see tabs Toán (n) · Vật lý (m), the last subject I used is selected, and only its questions are listed
```

**AC-02** — Switching clears subject-specific filters
```gherkin
Given Toán with topic "Hàm số" and a Toán tag chosen
When I switch to Vật lý
Then the topic and tag filters are removed and the other filters (loại, mức độ, đợt, năm học, trạng thái) stay
```

## US-02 — Filters in a sheet with counts
**Priority:** must

**AC-03** — Only this subject's topics and tags
```gherkin
Given Toán is chosen
When I open "Bộ lọc"
Then the topic tree shows Toán topics only, each with the number of questions in its subtree, and tags show Toán tags plus shared tags
```

**AC-04** — Apply, chips, clear
```gherkin
Given I tick "Hàm số", "Thi thử" and nguồn "Sở GD&ĐT Ninh Bình" in the sheet
When I press "Áp dụng"
Then the URL holds the filters, the list is filtered on the server, each choice appears as a chip with ×, and "Xóa lọc" removes all
```

**AC-05** — Counts follow the other filters
```gherkin
Given "Thi thử" is chosen
When I open the sheet
Then the numbers beside topics, types and tags count only Thi thử questions of the subject, while the "Đợt" section still shows every đợt with its count
```

## US-03 — Tags by subject
**Priority:** must

**AC-06** — Subject on tags
```gherkin
Given the Tags page
When I create a tag while Toán is chosen
Then it belongs to Toán unless I pick "Dùng chung"; the list can be filtered by subject
```

**AC-07** — Backfill
```gherkin
Given existing tags before the migration
When it runs
Then a tag whose questions are all Toán becomes a Toán tag, source tags and mixed tags stay shared
```

## US-04 — Exam matrix and school year
**Priority:** should

**AC-08** — Exam matrix by subject
```gherkin
Given an exam of subject Toán
When I edit its matrix
Then the topic picker and tag list only offer Toán topics and Toán/shared tags
```

**AC-09** — School year filter
```gherkin
Given questions imported from files of 2023-2024 and 2024-2025
When I filter Năm học 2024-2025
Then only questions whose source document is of 2024-2025 remain
```
