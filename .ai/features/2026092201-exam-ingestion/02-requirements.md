---
feature: exam-ingestion
stories: 6
acceptance_criteria: 22
---

# Requirements — Exam ingestion

## US-01 — Upload an exam file with its metadata

As a teacher, I want to upload a .docx/.pdf/image exam with subject, grade, semester and exam kind once, so every question inherits them.

**Priority:** must

**AC-01** — Upload queues a job
```gherkin
Given I am a teacher of "trungtama"
When I upload "de-mau-toan10.docx" with subject Toán, grade 10, semester HK1, kind "Giữa kỳ"
Then a document appears in /org/documents with status "Đang chờ" then "Đang xử lý" then "Đã tách"
And the original file is stored in object storage
```

**AC-02** — Validation
```gherkin
Given a file that is .doc, larger than 30 MB, or not a document/image
When I upload it
Then I see a field error explaining what is accepted and nothing is queued
```

**AC-03** — Duplicate file
```gherkin
Given "de-mau-toan10.docx" was already uploaded in my org
When I upload the same bytes again
Then I am taken to the existing document with a notice "File này đã được tải lên"
```

**AC-04** — Worker robustness
```gherkin
Given the worker crashes or a parser raises while processing
When the job is retried twice and still fails
Then the document status is "Lỗi" with a readable error and the stack trace is only in logs
And a job locked for more than 15 minutes is picked up again
```

## US-02 — Split Word exams into complete questions

As a teacher, I want every question of a Word exam split out with stem, options, answer, solution and images.

**Priority:** must

**AC-05** — MCQ split
```gherkin
Given a docx with 40 questions "Câu 1." … "Câu 40." each with options A–D
When it is parsed
Then 40 questions exist with number, stem and 4 options in order, type mcq
```

**AC-06** — Math and images
```gherkin
Given questions containing Word equations and inline pictures (in stem, in an option, in a solution)
When they are parsed
Then equations become $…$ LaTeX and each picture becomes an asset referenced in the right part
```

**AC-07** — Answers from inline marks, answer key, or formatting
```gherkin
Given answers given as "Đáp án: C" / "Chọn C" after a question, or a trailing answer key "1.A 2.C …" or a table, or the correct option underlined/bold
When the document is parsed
Then each question's answer is set and the answer source is recorded
```

**AC-08** — Solutions inline or trailing
```gherkin
Given solutions after each question ("Lời giải", "Hướng dẫn giải") or in a trailing "HƯỚNG DẪN GIẢI" section numbered from Câu 1
When the document is parsed
Then each solution is attached to its question and no duplicate questions are created
```

**AC-09** — THPT 2025 parts
```gherkin
Given a docx with PHẦN I (MCQ), PHẦN II (true/false a–d) and PHẦN III (short answer)
When it is parsed
Then types are mcq, true_false (4 statements with Đ/S when given) and short_answer (value) respectively, numbered within their part
```

**AC-10** — Confidence and issues
```gherkin
Given a question with 3 options, or no answer, or an unreadable fragment
When it is parsed
Then its confidence is below 0.85 and issues lists "thiếu phương án", "thiếu đáp án", etc.
And well-formed questions score ≥ 0.85
```

## US-03 — Read PDFs and scans

As a teacher, I want text PDFs and scanned exams read too.

**Priority:** must

**AC-11** — Text PDF
```gherkin
Given a PDF with a text layer and embedded figures
When it is parsed
Then text is extracted in reading order, figures are cropped into assets placed where they appear, and splitting works as for docx
```

**AC-12** — Scanned PDF or image
```gherkin
Given a PDF without a text layer, or a PNG/JPG photo of a printed exam
When it is parsed with OCR engine "tesseract"
Then text is OCR'd in Vietnamese, questions are split, and every question from OCR has an "OCR" issue flag and confidence ≤ 0.8
```

## US-04 — Choose AI models instead of hard-coding them

As a center admin, I want to register models and pick which one is used, so we can stay free (local) or plug in a paid provider later.

**Priority:** must

**AC-13** — Model registry
```gherkin
Given I am org_admin
When I add a model {provider ollama, model qwen2.5:7b, base URL http://ollama:11434, capability text}
Then it appears in /org/ai-models with a Free badge, and I can enable, disable, edit and delete it
And API keys are never returned by the API after saving
```

**AC-14** — Discover and test
```gherkin
Given an Ollama server is reachable
When I click "Phát hiện model Ollama"
Then locally pulled models are listed and can be added in one click
And "Kiểm tra" on a model returns ok with latency or the provider's error
```

**AC-15** — System models
```gherkin
Given super_admin registered a system-wide model
When any org lists available models
Then that model is included, marked "Hệ thống", and org admins cannot edit it
```

**AC-16** — Choose at upload
```gherkin
Given enabled models exist
When I upload a file and open "Cấu hình xử lý"
Then I can choose split mode (rule only / rule + AI fallback / AI all), OCR engine (auto / tesseract / AI vision) and the models for splitting and tagging
And the choice is stored on the document and on each question (parse_method, parse_model)
```

**AC-17** — Org defaults
```gherkin
Given I am org_admin
When I save default split mode, OCR engine, models and auto-approve threshold for my org
Then new uploads start with these defaults
```

## US-05 — AI fallback for hard questions

As a teacher, I want questions the rules could not split to be retried by the chosen model.

**Priority:** should

**AC-18** — Fallback
```gherkin
Given mode "rule + AI fallback" and a model is configured
When a question's rule-based confidence is below the threshold
Then the model is asked (JSON schema) to split that block, its result replaces the rule result when valid, and parse_method is "llm"
```

**AC-19** — Model failure
```gherkin
Given the model times out or returns invalid JSON
When the fallback runs
Then the next configured model is tried, and if none succeeds the rule result is kept with issue "AI không phản hồi"
```

**AC-20** — Re-parse
```gherkin
Given a parsed document
When I re-parse it with another model or mode
Then its draft questions are replaced, approved questions are kept, and the new config is recorded
```

## US-06 — Suggested topics and metadata on every question

As a teacher, I want each parsed question to already carry subject/grade/semester and a suggested leaf topic.

**Priority:** must

**AC-21** — Inherit metadata
```gherkin
Given the document was uploaded with Toán, grade 10, HK1, "Giữa kỳ", source name "THPT Chu Văn An"
When questions are created
Then each has subject, grade, semester, exam kind and a source tag "THPT Chu Văn An"
```

**AC-22** — Suggested topic
```gherkin
Given leaf topics exist in the org's tree
When a question mentions "nguyên hàm" / "tích phân" / "parabol" …
Then a primary topic suggestion with a score is stored (keyword rules; the tagging model when configured), shown on the document page
```

## Non-functional

| Kind | Requirement | Verified by |
| --- | --- | --- |
| Performance | 40-question docx parsed < 60 s without LLM | T-01-06 |
| Security | Uploaded files never executed; SVG/EMF not served as images; API keys encrypted | T-03-01 |
| Portability | Worker image builds on arm64 with pandoc + tesseract-vie | T-01-01 |
