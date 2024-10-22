def escape_json_string(s):
  # escape special characters in a string
  return s.replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

def to_json(data):
  # converting data to JSON string
  if isinstance(data, dict):
    return '{' + ','.join(f'"{key}":{to_json(value)}' for key, value in data.items()) + '}'
  elif isinstance(data, list):
    return '[' + ','.join(to_json(item) for item in data) + ']'
  elif isinstance(data, str):
    return f'"{escape_json_string(data)}"'
  elif isinstance(data, (int, float)):
    return str(data)
  elif data is None:
    return 'null'
  elif isinstance(data, bool):
    return 'true' if data else 'false'
  else:
    raise ValueError(f"Unsupported type for JSON serialization: {type(data)}")