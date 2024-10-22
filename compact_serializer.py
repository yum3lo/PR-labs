class CompactSerialize:
  @staticmethod
  def serialize(data):
    if isinstance(data, dict):
      return "d" + "".join(f"{CompactSerialize.serialize(key)}{CompactSerialize.serialize(value)}" for key, value in data.items()) + "e"
    elif isinstance(data, list):
      return "l" + "".join(CompactSerialize.serialize(item) for item in data) + "e"
    elif isinstance(data, str):
      return f"s{len(data)}:{data}"
    elif isinstance(data, int):
      return f"i{data}e"
    elif isinstance(data, float):
      return f"f{data}e"
    elif data is None:
      return "n"
    elif isinstance(data, bool):
      return "t" if data else "f"
    else:
      raise ValueError(f"Unsupported type for serialization: {type(data)}")

  @staticmethod
  def deserialize(data):
    def parse(data, index):
      if data[index] == 'd':
        result = {}
        index += 1
        while data[index] != 'e':
          key, index = parse(data, index)
          value, index = parse(data, index)
          result[key] = value
        return result, index + 1
      elif data[index] == 'l':
        result = []
        index += 1
        while data[index] != 'e':
          value, index = parse(data, index)
          result.append(value)
        return result, index + 1
      elif data[index] == 's':
        colon = data.index(':', index)
        length = int(data[index+1:colon])
        return data[colon+1:colon+1+length], colon+1+length
      elif data[index] == 'i':
        end = data.index('e', index)
        return int(data[index+1:end]), end + 1
      elif data[index] == 'f':
        end = data.index('e', index)
        return float(data[index+1:end]), end + 1
      elif data[index] == 'n':
        return None, index + 1
      elif data[index] == 't':
        return True, index + 1
      elif data[index] == 'f':
        return False, index + 1
      else:
        raise ValueError(f"Invalid serialized data at index {index}")

    result, _ = parse(data, 0)
    return result