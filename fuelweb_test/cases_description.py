import os
import sys
from testrail import *


def get_all_modules(directory):
    """
    For some directory return all python modules
    :param directory:
    :return: list modules
    """
    modules = []
    for f in os.listdir(os.path.abspath(directory)):
        module_name, ext = os.path.splitext(f)
        if ext == '.py':
            module = __import__(module_name)
            modules.append(module)
    return modules


def get_pydocs(module):
    def classesinmodule(module):
        """
        Found in net. Anonymous(C)
        :param module:
        :return:
        """
        md = module.__dict__
        return [
            md[c] for c in md if (
                isinstance(md[c], type) and md[c].__module__ == module.__name__
            )
        ]
    test_cases = []
    for i in classesinmodule(module):
        for method in dir(i):
            if method and callable(getattr(i, method)) and not method.startswith("__") \ 
                    and method is not "check_run":
                tcdoc = getattr(i, method).__doc__
                if tcdoc:
                    tp = tcdoc.split("\n")
                    test_pydoc = "\n".join(o.strip() for o in tp)
                    test_case = {
                        "title": test_pydoc.split("\n")[0],
                        "type_id": 1,
                        "priority_id": 3,
                        "estimate": "3m",
                        "refs": "",
                        "custom_test_group": method,
                        "custom_test_case_description": test_pydoc
                    }
                    steps = []
                    for s in test_pydoc.split("\n"):
                        if s and s[0].isdigit():
                            step = {
                                "content": s,
                                "expected": "pass"
                            }
                            steps.append(step)
                    test_case["custom_test_case_steps"] = steps
                    test_cases.append(test_case)
    return test_cases


if __name__ == "__main__":
    directory = "/home/alan/git/fuel-main/fuelweb_test/tests/"
    if os.path.isdir(directory):
        sys.path.append(directory)
    else:
        raise OSError(2, 'No such file or directory', directory)
    modules = get_all_modules(directory)
    client = APIClient("https://mirantis.testrail.com/")
    client.user = "mos-qa@mirantis.com"
    client.password = "8888888"
    for l in modules:
        for case in get_pydocs(l):
            client.send_post('add_case/1', case)
