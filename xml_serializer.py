def escape_xml_string(s):
  """Escape special characters in a string for XML."""
  return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')

# processed_data will be the root
def to_xml(data, root_tag='root'):
  """Convert data to XML string."""
  def _to_xml(data, tag):
    if isinstance(data, dict):
      return f"<{tag}>" + ''.join(_to_xml(v, k) for k, v in data.items()) + f"</{tag}>"
    elif isinstance(data, list):
      return f"<{tag}>" + ''.join(_to_xml(item, 'item') for item in data) + f"</{tag}>"
    elif isinstance(data, str):
      return f"<{tag}>{escape_xml_string(data)}</{tag}>"
    elif isinstance(data, (int, float)):
      return f"<{tag}>{data}</{tag}>"
    elif data is None:
      return f"<{tag}></{tag}>"
    elif isinstance(data, bool):
      return f"<{tag}>{'true' if data else 'false'}</{tag}>"
    else:
      raise ValueError(f"Unsupported type for XML serialization: {type(data)}")

  return f'<?xml version="1.0" encoding="UTF-8"?>\n{_to_xml(data, root_tag)}'