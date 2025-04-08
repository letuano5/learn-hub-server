import json
from google import genai 

client = genai.Client(api_key=GOOGLE_GENAI_KEY)

def generate(text, num_questions, lang):
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
    "answer": "The number corresponding to the index of the correct answer in the options array",
    "explanation": "Explain why you choose that answer"
  }

  current_prompt = f'''You are an assistant specialized in generating exam-style questions and answers. Your response must only be a JSON object with the following property:

"questions": An array of JSON objects, where each JSON object represents a question and answer pair. The JSON object representing the question must have the following properties:

{json.dumps(multiple_choice_example, indent=2)}

For example, the structure of your response should look like this:

{json.dumps(question_example, indent=2)}

Now generate {num_questions} questions based on the following content:

<Begin Document>
{text}
<End Document>

Each question must be **self-contained** and must include enough context so that the reader can understand and answer it without needing to refer back to the original text.

### **Important requirements:**
1. **Include only the necessary context in the question**  
   - If a question refers to an example, code snippet, or concept, **provide only the relevant excerpt** that helps in answering the question.  
   - **DO NOT include the full explanation or definition from the document, especially if it already contains the answer.**  
   - Example: If the document states:  
     ```
     A class is a blueprint for creating objects. An object is an instance of a class.
     ```
     - ❌ **Incorrect Question:**  
       ```
       "A class is a blueprint for creating objects. An object is an instance of a class." Based on this, which of the following statements is correct?
       ```
       - ✅ **Correct Question:**  
       ```
       In Java, what is the relationship between a class and an object?
       ```
2. **No vague references**  
   - Avoid phrases like _"the provided example"_, _"as mentioned earlier"_, _"the given diagram"_.  
   - Instead, **restate key information concisely** in the question.

3. **DO NOT insert the full text from the document verbatim**  
   - If the document contains definitions, descriptions, or answers, **rephrase them instead of copying them directly.**  
   - Example:
     - ❌ Incorrect: `"According to the text, 'A loop is used to repeat a set of instructions multiple times.' What is a loop?"`  
     - ✅ Correct: `"What is the purpose of a loop in programming?"`

4. **If the document is in a different language from the requested output language:**  
   - **Translate or summarize the necessary context instead of copying the original text.**  
   - Example:
     - If the document is in Vietnamese:  
       ```
       Lớp đối tượng (class) là khuôn mẫu để sinh ra đối tượng; Đối tượng là thể hiện (instance) của một lớp.
       ```
     - ❌ Incorrect Question:  
       ```
       "Lớp đối tượng (class) là khuôn mẫu để sinh ra đối tượng; Đối tượng là thể hiện (instance) của một lớp." What is the relationship between a class and an object?
       ```
     - ✅ Correct Question:  
       ```
       In object-oriented programming, what is the relationship between a class and an object?
       ```

5. **Ensure natural phrasing**  
   - **DO NOT use phrases like** _"from the document"_, _"according to the text"_, _"the passage states that"_.  
   - The question and answer should sound natural and independent.

6. **If the text contains LaTeX,** use `$...$` (inline math mode) for mathematical symbols.

The overall focus should be on assessing understanding and critical thinking. The questions must closely align with the content and must not introduce unrelated topics.

The generated questions and answers must be in ${lang}. However, your response must still follow the JSON format provided above. This means that while the values should be in ${lang}, the keys must be the exact same as given above, in English.'''

  response = client.models.generate_content(
    model = "gemini-2.0-flash", contents=current_prompt
  )

  # print(current_prompt)

  return response.text
