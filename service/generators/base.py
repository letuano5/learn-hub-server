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

# TODO: Update when error occurred to another chars; fix strings like $t_i = \\\\arg \\\\min_j (S(u,j) = S(v,j))$


def load_json(json_string):
  try:
    return json.loads(json_string)
  except json.JSONDecodeError:
    escaped_json = json_string

    replacements = {
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t',
        '\\': '\\\\',
        '"': '\\"',
    }

    for old, new in replacements.items():
      escaped_json = escaped_json.replace(old, new)

    try:
      return json.loads(escaped_json)
    except json.JSONDecodeError:
      try:
        normalized = json_string.encode('utf-8').decode('unicode_escape')
        return json.loads(normalized)
      except:
        import re

        fixed_json = re.sub(r'([{,])\s*([^"{\s][^:]*?):',
                            r'\1"\2":', escaped_json)

        fixed_json = re.sub(r':\s*([^"][^,}\s]+)', r':"\1"', fixed_json)

        return json.loads(fixed_json)

def fix_json_array(jsons):
  questions = []
  for subquestion in jsons:
    data = load_json(subquestion.replace('```json', '').replace('```', ''))
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
