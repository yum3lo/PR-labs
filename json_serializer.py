def escape_json_string(s):
  """Escape special characters in a string for JSON."""
  return s.replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

def to_json(data):
  """Convert data to JSON string."""
  if isinstance(data, dict):
    return '{' + ','.join(f'"{k}":{to_json(v)}' for k, v in data.items()) + '}'
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