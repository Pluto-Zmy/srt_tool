def merge_ts(origin_file_path, ts_file_path, output_file_path):
    ts_lines = []
    with open(ts_file_path, 'r', encoding='utf-8') as ts_file:
        lines = ts_file.readlines()
        for line in lines:
            if ']' in line:
                content = line.split(']')[1]
                if not content.isspace():
                    ts_lines.append(content)

    output = []
    with open(origin_file_path, 'r', encoding='utf-8') as origin_file:
        lines = origin_file.readlines()
        seq = 1
        for line_seq in range(len(lines)):
            line = lines[line_seq]
            if '-->' in line:
                origin_content = lines[line_seq + 1]
                ts_content = ts_lines[seq - 1] if seq - 1 < len(ts_lines) else None

                output.append('{}\n'.format(seq))
                output.append(line)
                output.append(origin_content)
                if ts_content:
                    output.append(ts_content)
                output.append('\n')

                seq += 1
        output.append('\n')

    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        output_file.writelines(output)


if __name__ == '__main__':
    origin_file_path = '2.srt'
    ts_file_path = '2_ts.txt'
    merge_ts(origin_file_path, ts_file_path, '2_merge.srt')