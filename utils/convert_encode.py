import codecs
import chardet

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        confidence = result['confidence']
    return encoding, confidence

def convert_gb18030_to_utf8(input_file, output_file):
    origin_encoding, confidence = detect_encoding(input_file)
    if origin_encoding == 'utf-8' and confidence >= 0.9:
        with codecs.open(input_file, 'r', 'utf-8') as f:
            content = f.read()
        with codecs.open(output_file, 'w', 'utf-8') as f:
            f.write(content)
        return
    with codecs.open(input_file, 'r', 'gb18030') as f:
        content = f.read()

    with codecs.open(output_file, 'w', 'utf-8') as f:
        f.write(content)


if __name__ == '__main__':
    for i in range(1, 9):
        convert_gb18030_to_utf8('{}.srt'.format(i), '{}.srt'.format(i))