import os

import law
import luigi

from framework import BaseTask


class ShellTask(BaseTask):
    """
    A task that provides convenience methods to work with shell commands, i.e., printing them on the
    command line and executing them with error handling.
    """

    cwd = luigi.Parameter(
        default="",
        description="custom working directory; if empty, will use a temporary directory; defaults to empty",
    )
    custom_args = luigi.Parameter(
        default="",
        description="custom arguments that are forwarded to the underlying command; they might not "
        "be encoded into output file paths; no default",
    )

    exclude_index = True
    exclude_params_req = {"cwd", "custom_args"}

    # by default, do not run in a tmp dir
    run_command_in_tmp = False
    cleanup_tmp_on_error = True

    # Command
    def build_command(self, fallback_level):
        # this method should build and return the command to run
        raise NotImplementedError

    def get_command(self, *args, **kwargs):
        # this method is returning the actual, possibly cleaned command
        return self.build_command(*args, **kwargs)

    def allow_fallback_command(self, errors):
        # by default, never allow fallbacks
        return False

    def touch_output_dirs(self):
        # keep track of created uris so we can avoid creating them twice
        handled_parent_uris = set()

        for outp in law.util.flatten(self.output()):
            # get the parent directory target
            parent = None
            if isinstance(outp, law.SiblingFileCollection):
                parent = outp.dir
            elif isinstance(outp, law.FileSystemFileTarget):
                parent = outp.parent

            # create it
            if parent and parent.uri() not in handled_parent_uris:
                parent.touch()
                handled_parent_uris.add(parent.uri())

    def run_command(self, cmd, highlighted_cmd=None, optional=False, **kwargs):
        # proper command encoding
        cmd = (
            law.util.quote_cmd(cmd) if isinstance(cmd, (list, tuple)) else cmd
        ).strip()

        # default highlighted command
        if not highlighted_cmd:
            highlighted_cmd = law.util.colored(cmd, "cyan")

        # when no cwd was set and run_command_in_tmp is True, create a tmp dir
        tmp_dir = None
        if self.cwd != "":
            tmp_dir = law.LocalDirectoryTarget(path=self.cwd)
            tmp_dir.touch()
            kwargs["cwd"] = tmp_dir.path
        elif "cwd" not in kwargs and self.run_command_in_tmp:
            tmp_dir = law.LocalDirectoryTarget(is_tmp=True)
            tmp_dir.touch()
            kwargs["cwd"] = tmp_dir.path
        self.publish_message("cwd: {}".format(kwargs.get("cwd", os.getcwd())))

        # call it
        with self.publish_step("running '{}' ...".format(highlighted_cmd)):
            p, lines = law.util.readable_popen(
                cmd, shell=True, executable="/bin/bash", **kwargs
            )
            for line in lines:
                print(line)

        # raise an exception when the call failed and optional is not True
        print("RETURN CODE:", p.returncode)
        if p.returncode != 0 and not optional:
            # when requested, make the tmp_dir non-temporary to allow for checks later on
            if tmp_dir and not self.cleanup_tmp_on_error:
                tmp_dir.is_tmp = False

            # raise exception
            raise ShellException(cmd, p.returncode, kwargs.get("cwd"))

        return p

    """
    @law.decorator.log
    @law.decorator.notify
    @law.decorator.localize
    """

    def run(self, **kwargs):
        self.pre_run_command()

        # default run implementation
        # first, create all output directories
        self.touch_output_dirs()

        # start command building and execution in a fallback loop
        errors = []
        while True:
            # get the command
            cmd = self.get_command(fallback_level=len(errors))
            if isinstance(cmd, tuple) and len(cmd) == 2:
                kwargs["highlighted_cmd"] = cmd[1]
                cmd = cmd[0]

            # run it
            try:
                self.run_command(cmd, **kwargs)
                break
            except ShellException as e:
                errors.append(e)
                if self.allow_fallback_command(errors):
                    self.logger.warning(str(e))
                    self.logger.info("starting fallback command {}".format(len(errors)))
                else:
                    raise e

        self.post_run_command()

    def pre_run_command(self):
        return

    def post_run_command(self):
        return


class ShellException(Exception):
    def __init__(self, cmd, returncode, cwd=None):
        self.cmd = cmd
        self.returncode = returncode
        self.cwd = cwd or os.getcwd()

        msg = "command execution failed"
        msg += "\nexit code: {}".format(self.returncode)
        msg += "\ncwd      : {}".format(self.cwd)
        msg += "\ncommand  : {}".format(self.cmd)

        super(ShellException, self).__init__(msg)
