# Source Document Extraction Prompt

You are extracting a structured briefing from a source document. This briefing will feed into marketing asset generation. Be precise and pull actual content — do not summarize into vagueness.

## Instructions

Read the source document provided and extract the following:

### 1. THESIS
The single core argument of this document in 1–2 sentences. What is the author trying to convince the reader of? State it as a claim, not a description.

### 2. CORE CLAIMS
3–5 key claims the document makes to support the thesis. Each should be a standalone assertion that could anchor a paragraph in a blog post or an email hook. Write each as a single declarative sentence.

### 3. DATA POINTS
Every specific statistic, dollar figure, percentage, date, or quantified claim in the document. Format as a bullet list. Include the context needed to use each data point in marketing copy (not just the number — include what it measures and why it matters).

### 4. QUOTABLE PHRASES
3–5 phrases or sentences from the document that are compelling enough to reuse in marketing assets. These should be vivid, specific, and non-generic. If the document has no quotable phrases, note that and move on.

### 5. COUNTERINTUITIVE INSIGHT
The single most surprising, contrarian, or non-obvious finding in the document. This is the insight that would make someone stop scrolling on LinkedIn. Frame it as: "Most people assume X, but this document shows Y because Z."

### 6. TARGET AUDIENCE
Who was this document written for? What role, industry, and level of seniority? This helps calibrate how to repackage the content for different ICPs.

### 7. PUREFACTS RELEVANCE
Cross-reference the document's subject matter with `/context/positioning.md`. How does this content connect to PureFacts' products, value propositions, or market position? Identify 2–3 specific connection points. This section ensures every asset ties back to PureFacts, not just the topic.

## Output Format

Return the extraction as a structured document with the 7 numbered headers above. Use bullets within each section. Do not editorialize or add content that is not in the source document (except section 7, which requires cross-referencing context).
