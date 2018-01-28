#!/usr/bin/env python3.5

import argparse
import logging
import os
import os.path
import shutil
import tempfile
import traceback


class FileAutomaton(object):

    def __init__(self, fct,
                 dir_input, dir_output, dir_error, dir_archive,
                 dir_temporary="/tmp"):

        self.logger = logging.getLogger(self.__class__.__name__)

        self.fct = fct

        self.dir_input = dir_input
        self.dir_output = dir_output
        self.dir_error = dir_error
        self.dir_archive = dir_archive
        self.dir_tmp_root = dir_temporary

        self.logger.info("Input directory: %s" % self.dir_input)
        self.logger.info("Onput directory: %s" % self.dir_output)
        self.logger.info("Error directory: %s" % self.dir_error)
        self.logger.info("Archive directory: %s" % self.dir_archive)
        self.logger.info("Temporary directory: %s" % self.dir_tmp_root)

        if not os.path.exists(self.dir_input):
            raise RuntimeError(
                "Input directory %s does not exist" % self.dir_input)

        for directory in [self.dir_output, self.dir_tmp_root,
                          self.dir_error, self.dir_archive]:

            if os.path.exists(directory):
                continue

            self.logger.info(
                "Directory %s does not exist. Creating it" % directory)

            os.makedirs(directory)

        self.dir_tmp_run = None
        self.dir_tmp_run_in = None
        self.dir_tmp_run_out = None

    def next(self):

        for one_file in os.listdir(self.dir_input):

            yield [os.path.join(self.dir_input, one_file)]

    def prepare(self, list_path_input):

        self.dir_tmp_run = tempfile.mkdtemp(
            dir=self.dir_tmp_root, prefix="automaton_")

        self.dir_tmp_in = os.path.join(self.dir_tmp_run, "in")
        self.dir_tmp_out = os.path.join(self.dir_tmp_run, "out")

        os.makedirs(self.dir_tmp_in)
        os.makedirs(self.dir_tmp_out)

        list_path_prepared = []

        for path_input in list_path_input:

            path_tmp_in = os.path.join(
                self.dir_tmp_in, os.path.basename(path_input))
            shutil.move(path_input, path_tmp_in, shutil.copyfile)

            list_path_prepared.append(path_tmp_in)

        return list_path_prepared

    def finalize(self, success, list_path_input, list_path_output):

        if success is True:
            dir_destination = self.dir_archive
        elif success is False:
            dir_destination = self.dir_error
        else:
            raise RuntimeError("Bad return value: %s" % success)

        for one_path in list_path_output:
            shutil.move(one_path, self.dir_output, shutil.copyfile)

        for one_path in list_path_input:
            shutil.move(one_path, dir_destination, shutil.copyfile)

        if success is True:
            shutil.rmtree(self.dir_tmp_run)

    def run(self):

        for list_path_input in self.next():

            self.logger.info("Input: %s" % ", ".join(list_path_input))
            list_path_prepared = self.prepare(list_path_input)

            self.logger.debug(
                "Prepared input: %s" % ", ".join(list_path_prepared))

            try:
                success, list_path_output = self.fct(
                    list_path_prepared, self.dir_tmp_out)
            except:
                success = False
                self.logger.error(traceback.format_exc())

            self.finalize(success, list_path_prepared, list_path_output)


def process_ok(list_path_prepared, dir_output):

    filename = os.path.basename(
        list_path_prepared[0])

    output_path = os.path.join(dir_output, filename + ".out")
    fd = open(output_path, "w")
    fd.write("Hello World !")
    fd.close()

    return True, [output_path]


def process_err(list_path_prepared, dir_output):

    return False, []


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("--log", "-l", help="Log file")
    parser.add_argument(
        "--err", "-e", action="store_true", help="Tests error case")
    args = parser.parse_args()

    if args.log is not None:
        logging.basicConfig(filename=args.log, level=logging.DEBUG)

    if args.err is True:
        fct = process_err
    else:
        fct = process_ok

    fa = FileAutomaton(fct, "input", "output", "error", "archive")
    fa.run()
