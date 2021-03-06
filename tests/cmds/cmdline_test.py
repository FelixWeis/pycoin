import unittest
import os
import subprocess
import sys
import tempfile

from pycoin.cmds import ku, tx

from .ToolTest import ToolTest


def get_test_cases():
    TESTS_PATH = os.path.join(os.path.dirname(__file__), "test_cases")
    paths = []
    for dirpath, dirnames, filenames in os.walk(TESTS_PATH):
        for fn in filenames:
            if fn.endswith(".txt") and fn[0] != '.':
                paths.append(os.path.join(dirpath, fn))
    paths.sort()
    l = []
    for p in paths:
        with open(p) as f:
            # allow "#" comments at the beginning of the file
            while 1:
                cmd = f.readline()[:-1]
                if cmd[0] != '#':
                    break
            expected_output = f.read()
            test_name = os.path.relpath(
                p, TESTS_PATH).replace(".", "_").replace("/", "_")
            l.append((test_name, cmd, expected_output))
    return l


TOOL_LOOKUP = {
    "tx" : (tx.create_parser(), tx.tx),
    "ku" : (ku.create_parser(), lambda args, parser: ku.ku(args))
}


class CmdlineTest(ToolTest):
    def invoke_tool(self, args):
        tool_name = args[0]
        if tool_name.endswith(".py"):
            tool_name = tool_name[:-3]
        parser, main = TOOL_LOOKUP[tool_name]
        return main(parser.parse_args(args[1:]), parser)


def make_f(cmd, expected_output):

    def f(self):
        CACHE_DIR = tempfile.mkdtemp()
        old_environ = dict(os.environ)
        new_environ = dict(PYCOIN_CACHE_DIR=CACHE_DIR)
        for k in "PATH PYCOIN_BTC_PROVIDERS".split():
            new_environ[k] = os.environ.get(k, "")
        os.environ = new_environ
        os.chdir(CACHE_DIR)
        for c in cmd.split(";"):
            actual_output = self.launch_tool(c)
        if actual_output != expected_output:
            print(repr(cmd))
            print(repr(actual_output))
            print(repr(expected_output))
        os.environ = old_environ
        self.assertEqual(expected_output, actual_output)
    return f


def inject():
    for idx, (name, i, o) in enumerate(get_test_cases()):
        name_of_f = "test_%s" % name
        setattr(CmdlineTest, name_of_f, make_f(i, o))
        print("adding %s" % name_of_f)

inject()


def main():
    unittest.main()

if __name__ == "__main__":
    main()
