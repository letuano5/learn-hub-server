import google.generativeai as genai
import json


class GenAIClient:
  def __init__(self, api_key: str, default_prompt: str = ''):
    genai.configure(api_key=api_key)

    if len(default_prompt) > 0:
      self.model = genai.GenerativeModel(
          'gemini-2.0-flash', system_instruction=default_prompt)
    else:
      self.model = genai.GenerativeModel('gemini-2.0-flash')

# TODO: Update when error occurred to another chars (" for example)
def load_json(json_string):
  return json.loads(json_string.replace('\\', '\\\\'))  

def fix_json_array(jsons):
  questions = []
  for subquestion in jsons:
    subquestion = subquestion.replace('```json', '').replace('```', '')
    print(subquestion)
    data = load_json(subquestion)
    print(data)
    # print(subquestion)

    for item in data['questions']:
      questions.append({
          "question": item["question"],
          "options": item["options"],
          "answer": item["answer"],
          "explanation": item["explanation"]
      })

  merged = {"questions": questions}

  return merged

