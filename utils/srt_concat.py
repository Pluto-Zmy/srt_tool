def srt_concat(srt_files):
    global_line_seq = 1
    output = []
    for file_name in srt_files:
        with open(file_name, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            for line_seq in range(len(lines)):
                line = lines[line_seq]
                if '-->' in line:
                    line_offset = 1
                    output.append('{}\n'.format(global_line_seq))
                    output.append(line)
                    while line_seq + line_offset < len(lines) and not lines[line_seq + line_offset].isspace():
                        next_line = lines[line_seq + line_offset]
                        output.append(next_line)
                        line_offset += 1
                    output.append('\n')
                    global_line_seq += 1

    with open('output.srt', 'w', encoding='utf-8') as output_file:
        output_file.writelines(output)


if __name__ == '__main__':
    srt_files = ['1.srt', 'merge_2.srt', '3.srt', '4.srt', '5.srt', '6.srt', '7.srt', '8.srt', '9.srt']
    srt_concat(srt_files)