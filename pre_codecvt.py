import os
import chardet

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
    return encoding, confidence

def convert_file(input_path, output_path):
    with open(input_path, 'r', encoding='gb18030') as file:
        content = file.read()

    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(content)

folder = './'

for filename in os.listdir(folder):
    if filename.endswith("srt"):
        input_path = os.path.join(folder, filename)
        origin_encoding, confidence = detect_encoding(input_path)
        if origin_encoding == 'utf-8' and confidence >= 0.9:
            continue
        output_path = os.path.join(folder, filename)
        convert_file(input_path, output_path)