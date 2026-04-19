import json

from utils.merge_ts import merge_ts
from utils.mp3_duration import get_mp3_duration
from utils.srt_offset import set_srt_offset
from utils.srt_concat import srt_concat
from utils.convert_encode import convert_gb18030_to_utf8
from utils.timecvt import timecvt
from utils.fix_srt_overlap import fix_srt_overlap


def srt_tool(data):
    output_srt_path = []

    base_fps = data.get('base_fps', 60)
    srt_list = data.get('srt_list', None)

    for srt in srt_list:
        file_name = srt.get('file_name', None)
        ts_file_name = srt.get('ts_file_name', None)
        time_code = srt.get('time_code', None)

        if not file_name or not time_code:
            continue

        file_name_utf8 = '{}_utf8.srt'.format(file_name.split('.')[0])
        convert_gb18030_to_utf8(file_name, file_name_utf8)

        time_offset = timecvt(time_code, base_fps)

        if ts_file_name:
            merge_srt_path = '{}_merge.srt'.format(file_name_utf8.split('.')[0])
            merge_ts(file_name_utf8, ts_file_name, merge_srt_path)
            final_srt_path = '{}_offset.srt'.format(merge_srt_path.split('.')[0])
            set_srt_offset(merge_srt_path, time_offset, final_srt_path)
        else:
            final_srt_path = '{}_offset.srt'.format(file_name_utf8.split('.')[0])
            set_srt_offset(file_name_utf8, time_offset, final_srt_path)

        output_srt_path.append(final_srt_path)

    srt_concat(output_srt_path)
    fix_srt_overlap('output.srt')



if __name__ == '__main__':
    config_path = './config.json'
    with open(config_path, 'r', encoding='utf8') as file:
        data = json.load(file)
        srt_tool(data)