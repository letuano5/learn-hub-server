import google.generativeai as genai
import json

class GenAIClient:
  def __init__(self, api_key: str, default_prompt: str = ''):
    genai.configure(api_key=api_key)

    if len(default_prompt) > 0:
      self.model = genai.GenerativeModel('gemini-2.0-flash', system_instruction=default_prompt)
    else:
      self.model = genai.GenerativeModel('gemini-2.0-flash')

# TODO: Update when error occurred to another chars; fix strings like $t_i = \\\\arg \\\\min_j (S(u,j) = S(v,j))$
def escape_json_string(json_string):
  return json_string.replace('\\', '\\' + '\\')

def fix_json_array(jsons):
  questions = []
  for subquestion in jsons:
    subquestion = escape_json_string(subquestion.replace('```json', '').replace('```', ''))
    print(subquestion)
    data = json.loads(subquestion)
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
