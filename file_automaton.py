#!/usr/bin/env python3.5

import abc
import logging
import os
import os.path
import shutil
import tempfile
import traceback


class FileAutomaton(object, metaclass=abc.ABCMeta):

    def __init__(self,
                 dir_input, dir_output, dir_valid, dir_invalid,
                 dir_temporary="/tmp"):

        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize directories
        self.dir_input = dir_input
        self.dir_output = dir_output
        self.dir_valid = dir_valid
        self.dir_invalid = dir_invalid
        self.dir_tmp_root = dir_temporary

        self.logger.info("Input directory: %s" % self.dir_input)
        self.logger.info("Output directory: %s" % self.dir_output)
        self.logger.info("Valid files directory: %s" % self.dir_valid)
        self.logger.info("Invalid files directory: %s" % self.dir_invalid)
        self.logger.info("Temporary directory: %s" % self.dir_tmp_root)

        if not os.path.exists(self.dir_input):
            raise RuntimeError(
                "Input directory %s does not exist" % self.dir_input)

        # Create missing directories
        for directory in [self.dir_output, self.dir_tmp_root,
                          self.dir_valid, self.dir_invalid]:

            if os.path.exists(directory):
                continue

            self.logger.info(
                "Directory %s does not exist. Creating it" % directory)

            os.makedirs(directory)

        self.dir_tmp_run = None
        self.dir_tmp_run_in = None
        self.dir_tmp_run_out = None

    def next(self):
        """Return a list of files to be processed"""

        for one_file in os.listdir(self.dir_input):

            yield [os.path.join(self.dir_input, one_file)]

    def prepare(self, list_path_input):
        """Retrieve input files and copy them to temporary directory"""

        # Prepare temporary directories
        self.dir_tmp_run = tempfile.mkdtemp(
            dir=self.dir_tmp_root, prefix="automaton_")

        self.dir_tmp_run_in = os.path.join(self.dir_tmp_run, "in")
        self.dir_tmp_run_out = os.path.join(self.dir_tmp_run, "out")

        self.logger.debug("Creating directory %s" % self.dir_tmp_run_in)
        os.makedirs(self.dir_tmp_run_in)

        self.logger.debug("Creating directory %s" % self.dir_tmp_run_out)
        os.makedirs(self.dir_tmp_run_out)

        # Move input files to temporary directory
        list_path_prepared = []

        for path_input in list_path_input:

            path_tmp_in = os.path.join(
                self.dir_tmp_run_in, os.path.basename(path_input))

            self.logger.debug("Moving %s to %s" % (path_input, path_tmp_in))
            shutil.move(path_input, path_tmp_in, shutil.copyfile)

            list_path_prepared.append(path_tmp_in)

        return list_path_prepared

    def finalize(self, success, list_path_input, list_path_output):
        """Move files to their final destination"""

        if success is True:
            dir_destination = self.dir_valid
        elif success is False:
            dir_destination = self.dir_invalid
        else:
            raise RuntimeError("Bad return value: %s" % success)

        self.logger.info("Processing returned %s" % success)
        self.logger.info("Input files will be moved to %s" % dir_destination)

        for one_path in list_path_output:
            self.logger.info("Moving %s to %s" % (one_path, self.dir_output))
            shutil.move(one_path, self.dir_output, shutil.copyfile)

        for one_path in list_path_input:
            self.logger.info("Moving %s to %s" % (one_path, dir_destination))
            shutil.move(one_path, dir_destination, shutil.copyfile)

        if success is True:
            self.logger.debug(
                "Removing temporary directory %s" % self.dir_tmp_run)
            shutil.rmtree(self.dir_tmp_run)

    def run(self):

        for list_path_input in self.next():

            self.logger.info("Input: %s" % ", ".join(list_path_input))
            list_path_prepared = self.prepare(list_path_input)

            self.logger.debug(
                "Prepared input: %s" % ", ".join(list_path_prepared))

            try:
                success, list_path_output = self.process(
                    list_path_prepared)
            except:
                success = False
                list_path_output = []
                self.logger.error(traceback.format_exc())

            if success is True:
                self.logger.info("Processing succeeded")
                self.logger.info("Ouput: %s" % ", ".join(list_path_output))
            else:
                self.logger.info("Processing failed")

            self.finalize(success, list_path_prepared, list_path_output)

    @abc.abstractmethod
    def process(self, list_path_prepared):
        """Main processing. Must be overwritten"""

        return True, []
