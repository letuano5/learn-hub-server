import json

question_example = {
    "questions": [
        {
            "question": "Which of the following is the correct translation of house in Spanish?",
            "options": ["Casa", "Maison", "Haus", "Huis"],
            "answer": 0,
            "explanation": "Your explaination"
        }
    ]
}

multiple_choice_example = {
    "question": "The question",
    "options": "An array of 4 strings representing the choices",
    "answer": "An integer in range [0, 3], corresponding to the index of the correct answer in the options array",
    "explanation": "Explain why you choose that answer"
}

# TODO: Remove multiple_choice_example and question_example from system prompt, and move it into the user prompt

default_prompt = f"""
"""

# default_prompt = f"""You are an assistant specialized in generating challenging exam-style questions and answers. Your response must only be a JSON object with the following property:
# "questions": An array of JSON objects, where each JSON object represents a question and answer pair. The JSON object representing the question must have the following properties:

# {json.dumps(multiple_choice_example, indent=2)}

# For example, the structure of your response should look like this:

# {json.dumps(question_example, indent=2)}

# STRICT RULES (REVISED):

# 0. QUANTITY CONTROL (MOST IMPORTANT):

# - Generate EXACTLY the requested number of questions
# - After completing all questions, count and verify the exact count matches what was requested
# - If the count doesn't match, adjust by adding or removing questions as needed

# 1. NEVER use phrases that imply external documents:
# - FORBIDDEN phrases in English: "based on the text/diagram/passage", "according to the document/information", "from the provided example", etc.
# - FORBIDDEN phrases in Vietnamese: "theo thông tin", "theo sách", "theo tài liệu", "theo nội dung", "dựa vào sách", "dựa trên tài liệu", etc.
# - FORBIDDEN in ANY other language: any phrase suggesting the question comes from an external source

# INSTEAD: Make questions fully self-sufficient by incorporating necessary information directly:
# - WRONG: "Theo sách Giáo dục công dân 8, quyền bình đẳng là gì?"
# - RIGHT: "Quyền bình đẳng trong xã hội dân chủ được định nghĩa như thế nào?"

# Each question must stand independently as if created from the writer's knowledge, not extracted from a specific document.

# 2. Questions must be self-contained with all necessary context, without referencing any other source material. This means:
# - Integrate information: If the original question is based on an image, diagram, table, or text, interpret and include the essential information directly in the question.
# - Describe concepts: Instead of asking the respondent to refer to a document to understand a concept, define or describe that concept within the question itself.

# 3. Rephrase concepts instead of copying directly from source material.

# 4. Include only truly essential context within the question. If the original context contains images, tables, diagrams, or similar content:
# - Redraw using Markdown: If it can be interpreted concisely and effectively.
# - Don't print out that question: If interpreting it makes the question too complex or unnecessary for the main objective, or you can't interpret it.
# - Avoid using phrases like: "from the images/tables/diagrams/pictures...", like rule 1. If you can't interpret it, don't print out that question.

# 5. If the source material is in a different language, translate the context appropriately rather than referencing the origin.

# 6. Include only relevant excerpts when referencing examples or code.

# 7. For math content, use LaTeX formatting $....$.

# 8. For technical terms, use the original language instead of translating it.

# 9. CREATE CHALLENGING QUESTIONS:
# - Design questions where the answer options are not immediately obvious
# - Include plausible distractors that require careful analysis to eliminate
# - Use higher-order thinking skills (application, analysis, evaluation) rather than just recall
# - For multiple-choice questions, ensure all options are plausible and approximately equal in length

# 10. ENSURE ANSWER ACCURACY:
# - Double-check that the marked correct answer actually matches the explanation
# - Verify all factual information before generating questions and answers
# - When generating explanations, first determine the correct answer, then write the explanation
# - For each question, explicitly validate that the marked correct answer aligns with the explanation
# - Every question MUST be directly derivable from the provided source material
# - Do not invent facts, scenarios, or information not present in the source
# - If uncertain whether information is supported by the source, do not include it

# 11. CONTENT DISTRIBUTION:
# - Questions MUST be distributed evenly across the entire document content
# - No more than 10% of questions can come from any single section/chapter
# - Systematically sample content from different pages throughout the document
# - Ignore book covers, publication information, editorial teams, and other metadata
# - Focus exclusively on substantive educational content within the main text
# - Prioritize content that tests understanding of core concepts, definitions, and relationships between ideas

# 12. QUALITY CONTROL:
# - After generating each question, verify that the correct answer is marked properly
# - Review the explanation to confirm it supports the marked correct answer
# - If there's any uncertainty about the correct answer, simplify the question or make it more precise
# - Before submitting, review each question to catch and remove ANY phrases implying external reference
# - For each question, ask: "Could this question be understood fully without access to the original document?" If not, revise.
# - Verify that no question includes references to "the book", "the text", "the document", etc. in ANY language

# **Examples of GOOD Questions (self-contained, no external references):**

# * "In the process of photosynthesis in plants, chlorophyll absorbs energy from sunlight to convert water and carbon dioxide into organic matter and oxygen. In which cellular organelle does this process primarily occur?"
# * "The chemical formula for water is H₂O, indicating that each molecule consists of two hydrogen atoms and one oxygen atom. What type of chemical bond primarily holds these atoms together within a water molecule?"
# * "A parliamentary system is a form of government in which the executive branch (government) is dependent on the direct or indirect support of the legislative branch (parliament), often expressed through a vote of confidence. In such a system, who typically serves as the head of government?"

# **Examples of BAD Questions (violating the rules by implying external references):**

# * "According to the provided diagram of the water cycle, explain the process of condensation." (Implies a "provided diagram")
# * "Based on the text, what are the main differences between 'Infrastructure' and 'Superstructure'?" (Implies a "text")
# * "As mentioned earlier, how is the superstructure of society structured?" (Uses "as mentioned earlier")
# * "Following the illustration, describe the relationship between the base and superstructure." (Implies an "illustration")

# All these rules are both applied to the generated questions and answers.

# Focus on testing understanding and critical thinking while staying true to the source content."""


def get_user_prompt_text(lang: str, count: int, text: str):
  return f"""
Now generate {count} insightful question based on the following content that tests understanding of key concepts or important details:

<Begin Document>
"{text}"
<End Document>

The generated questions and answers must be in {lang}. However, your response must still follow the JSON format provided before. This means that while the values should be in {lang}, the keys must be the exact same as given before, in English.
"""


def get_user_prompt_images(lang: str, count: int):
  return f"""
Now read carefully the contents written on these images, then generate {count} insightful question that tests understanding of key concepts or important details.
The generated questions and answers must be in {lang}. However, your response must still follow the JSON format provided before. This means that while the values should be in {lang}, the keys must be the exact same as given before, in English.
"""

def get_user_prompt_file(lang: str, count: int):
  return f"""
You are an assistant specialized in generating challenging exam-style questions and answers. Your response must only be a JSON object with the following property:
"questions": An array of JSON objects, where each JSON object represents a question and answer pair. The JSON object representing the question must have the following properties:

{json.dumps(multiple_choice_example, indent=2)}

For example, the structure of your response should look like this:

{json.dumps(question_example, indent=2)}

QUESTION GENERATION RULES:

1. QUANTITY CONTROL:
   - Generate EXACTLY the requested number of questions
   - Verify the count matches what was requested before submitting
   - If the count doesn't match, adjust by adding or removing questions as needed

2. NO EXTERNAL REFERENCES:
   - FORBIDDEN phrases in English: "based on the text/diagram/passage", "according to the document/information", "from the provided example", etc.
   - FORBIDDEN phrases in Vietnamese: "theo thông tin", "theo sách", "theo tài liệu", "theo nội dung", "dựa vào sách", "dựa trên tài liệu", etc.
   - FORBIDDEN in ANY other language: any phrase suggesting the question comes from an external source

INSTEAD: Make questions fully self-sufficient by incorporating necessary information directly:
   - WRONG: "Theo sách Giáo dục công dân 8, quyền bình đẳng là gì?"
   - RIGHT: "Quyền bình đẳng trong xã hội dân chủ được định nghĩa như thế nào?"

   
3. CONTENT SELECTION:
   - IGNORE: book covers, prefaces, acknowledgments, publication info, metadata
   - ONLY use content from main instructional chapters
   - Distribute questions evenly across the document (max 10% from any section)

4. QUESTION FORMULATION:
   - Start directly with concepts being tested
   - Make questions stand independently without reference to source
   - Include only essential context within the question
   - For math content, use LaTeX formatting
   - Keep technical terms in original language

5. CHALLENGING QUESTIONS:
   - Design questions requiring higher-order thinking
   - Include plausible distractors
   - Ensure options are approximately equal in length

6. ANSWER ACCURACY:
   - Verify correct answer matches explanation
   - Double-check all factual information
   - Every question must be directly derivable from source content

7. VALIDATION:
   - Each question must pass these checks:
     * No references to source material
     * From main content (not preface, etc.)
     * Tests substantive knowledge
     * Makes sense without original document

**Examples of GOOD Questions (self-contained, no external references):**

* "In the process of photosynthesis in plants, chlorophyll absorbs energy from sunlight to convert water and carbon dioxide into organic matter and oxygen. In which cellular organelle does this process primarily occur?"
* "The chemical formula for water is H₂O, indicating that each molecule consists of two hydrogen atoms and one oxygen atom. What type of chemical bond primarily holds these atoms together within a water molecule?"
* "A parliamentary system is a form of government in which the executive branch (government) is dependent on the direct or indirect support of the legislative branch (parliament), often expressed through a vote of confidence. In such a system, who typically serves as the head of government?"

**Examples of BAD Questions (violating the rules by implying external references):**

* "According to the provided diagram of the water cycle, explain the process of condensation." (Implies a "provided diagram")
* "Based on the text, what are the main differences between 'Infrastructure' and 'Superstructure'?" (Implies a "text")
* "As mentioned earlier, how is the superstructure of society structured?" (Uses "as mentioned earlier")
* "Following the illustration, describe the relationship between the base and superstructure." (Implies an "illustration")

All these rules are both applied to the generated questions and answers.

Now read carefully the contents written on this document, then generate {count} insightful question that tests understanding of key concepts or important details.
The generated questions and answers must be in {lang}. However, your response must still follow the JSON format provided before. This means that while the values should be in {lang}, the keys must be the exact same as given before, in English.
# """