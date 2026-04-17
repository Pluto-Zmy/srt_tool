import os
import sys
import argparse
from datetime import datetime, timedelta
import pathlib
import codecs

from abc import abstractmethod


class SubtitleItem(object):
    def __init__(self):
        super().__init__()
        self.index = 0
        self.stime = 0
        self.etime = 0
        self.text = ""


class SubtitleImp(object):
    def __init__(self) -> None:
        super().__init__()
        self._subItems = []

    @abstractmethod
    def load_file(self, input_file):
        pass

    @abstractmethod
    def save_file(self, output_file=None):
        pass

    def adjust_time(self, ad_time):
        for sub_tmp in self._subItems:
            sub_tmp.stime += timedelta(seconds=ad_time)
            sub_tmp.etime += timedelta(seconds=ad_time)

    def set_sub_items(self, items):
        self._subItems = items

    def get_sub_items(self):
        return self._subItems


class SrtSubImp(SubtitleImp):
    def __init__(self):
        super().__init__()

    def parse(self, item_strs):
        srt_item = SubtitleItem()
        srt_item.index = int(item_strs[0])
        srt_item.text = item_strs[2]

        time_strs = item_strs[1].split("-->")

        srt_item.stime = datetime.strptime(time_strs[0].strip(), "%H:%M:%S,%f")
        srt_item.etime = datetime.strptime(time_strs[1].strip(), "%H:%M:%S,%f")
        return srt_item

    def load_file(self, input_file):
        rlines = []
        with open(input_file, "r", encoding="utf8") as f:
            rlines = f.readlines()

        data = rlines[0].encode(encoding="utf-8")
        if data[:3] == codecs.BOM_UTF8:
            rlines[0] = data[3:].decode(encoding="utf-8")
        i = 0
        while i < len(rlines):
            if rlines[i].strip() == "":
                i += 1
                continue

            srt_strs = []
            srt_strs.append(rlines[i].strip())
            i += 1
            srt_strs.append(rlines[i].strip())
            i += 1

            text_str = ""
            while rlines[i].strip() != "":
                text_str = text_str + rlines[i]
                i += 1
            srt_strs.append(text_str)

            self._subItems.append(self.parse(srt_strs))

    def save_file(self, output_file=None):
        with open(output_file, "w", encoding="utf8") as f:
            for sub_tmp in self._subItems:
                f.write("%d\n" % (sub_tmp.index))
                f.write(
                    "%s --> %s \n"
                    % (
                        sub_tmp.stime.strftime("%H:%M:%S,%f")[:-3],
                        sub_tmp.etime.strftime("%H:%M:%S,%f")[:-3],
                    )
                )
                f.write("%s\n" % (sub_tmp.text))


def gen_subtitle_imp_by_name(filename):
    filterstr = pathlib.Path(filename).suffix
    if filterstr == ".srt":
        return SrtSubImp()
    else:
        return None


def init_arg_table():
    """init argument table,return args."""
    parse = argparse.ArgumentParser(
        description="subtitle tools.",
        fromfile_prefix_chars="@",
    )

    parse.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        dest="inputfile",
        help="input subtitle file",
    )
    parse.add_argument(
        "-o",
        "--output",
        default="",
        type=str,
        required=False,
        dest="outputfile",
        help="output subtitle file",
    )
    parse.add_argument(
        "-t",
        "--time",
        default=0,
        type=float,
        required=False,
        dest="ad_time",
        help="adjustment time.",
    )

    return parse.parse_args()


def set_srt_offset(input_file_path, time, output_file_path):
    if not os.path.isfile(input_file_path):
        return

    sub_imp = gen_subtitle_imp_by_name(input_file_path)
    if sub_imp is None:
        return

    sub_imp.load_file(input_file_path)
    if time:
        sub_imp.adjust_time(time)
    sub_imp.save_file(output_file_path)


if __name__ == "__main__":
    args = init_arg_table()

    if not os.path.isfile(args.inputfile):
        print(args.inputfile + " isn't exist.\n")
        sys.exit(-1)

    if args.outputfile == "":
        args.outputfile = args.inputfile

    sub_imp = gen_subtitle_imp_by_name(args.inputfile)
    if sub_imp is None:
        print(args.inputfile + "is invalid subtitle file.\n")
        sys.exit(-1)

    sub_imp.load_file(args.inputfile)

    if args.ad_time != 0:
        sub_imp.adjust_time(args.ad_time)

    if pathlib.Path(args.inputfile).suffix == pathlib.Path(args.outputfile).suffix:
        sub_imp.save_file(args.outputfile)
    else:
        print("other format will support later..\n")

    print("save file to  %s  finished.\n " % (args.outputfile))
