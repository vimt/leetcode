import glob
import html
import json
import logging
import os
import subprocess

import click
import requests

logging.basicConfig(format="[%(asctime)s: %(levelname)s] %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)


def get_problem_detail(slug: str):
    url = "https://leetcode-cn.com/graphql"
    query = """
      query getQuestionDetail($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
          content
          stats
          codeDefinition
          sampleTestCase
          enableRunCode
          metaData
          translatedTitle
          translatedContent
          questionFrontendId
        }
      }
    """
    payload = {
        "query": query,
        "variables": {"titleSlug": slug},
        "operationName": "getQuestionDetail"
    }
    rsp = requests.post(url, json=payload)
    data = rsp.json()['data']['question']
    if not data['codeDefinition']:
        return None
    code = json.loads(data['codeDefinition'])
    return ProblemDetail(data['questionFrontendId'], data['translatedTitle'], data['content'],
                         {i['value']: i['defaultCode'] for i in code})


class Problem(object):
    def __init__(self, leetcode_data):
        self.id = leetcode_data['frontendQuestionId'].replace(' ', '_').lower()
        self.title = leetcode_data['title']
        self.key = leetcode_data['titleSlug']
        self.ch_title = leetcode_data['titleCn']


def trans_arg(arg: str, type: str, is_return: bool = False):
    arg = arg.strip()
    if '=' in arg:
        arg = arg.partition('=')[2].strip()
    if 'char' in type:
        arg = arg.replace('"', "'")
    if type.startswith("Vec"):
        if type == "Vec<String>" and not is_return:
            return f"svec!{arg}"
        elif type == "Vec<Vec<String>>":
            return f"vec![" + arg[1:-1].replace('[', 'svec![') + ']'
        elif type == "Vec<Option<Rc<RefCell<TreeNode>>>>":
            return 'vec![' + arg[1:-1].replace('[', 'tree![') + ']'
        elif type == "Vec<Option<Box<ListNode>>>":
            return 'vec![' + arg[1:-1].replace('[', 'link![') + ']'
        else:
            return arg.replace('[', 'vec![')
    elif type == "String":
        return f"String::from({arg})"
    elif type == "Option<Rc<RefCell<TreeNode>>>":
        return 'tree!' + arg
    elif type == "Option<Box<ListNode>>":
        return 'link!' + arg
    else:
        return arg


class ProblemDetail(object):
    def __init__(self, question_id, ch_title, content, templates):
        self.id = question_id.replace('????????? ', 'm').replace('?????? ', '').replace('.', '_').replace(' ', '_').lower()
        self.ch_title = ch_title
        self.content = content
        self.templates = templates

    def rust_template(self, cases=''):
        code: str = self.templates['rust']
        lines = code.split('\n')
        lines = [i.strip() for i in lines if not i.strip().startswith('//')]
        if 'impl Solution {' in lines:
            lines.remove('impl Solution {')
            lines.remove('}')
        if 'TreeNode' in code:
            lines.insert(0, "use leetcode::treenode::{leetcode_tree, TreeNode};")
            lines.insert(1, "use leetcode::tree;")
            lines.insert(2, "")
        if 'ListNode' in code:
            lines.insert(0, "use leetcode::linknode::{ListNode, vec_to_link};")
            lines.insert(1, "use leetcode::link;")
            lines.insert(2, "")
        if 'svec![' in cases:
            lines.insert(0, "use leetcode::svec;")
        return '\n'.join(lines)

    def rust_testcase(self, multi, unorder):
        code = self.templates['rust']
        funcs = [i for i in code.split('\n') if i.strip().startswith('pub fn')]
        if len(funcs) > 1:
            raise Exception("multi funcs")
        func: str = funcs[0]
        funcname, _, other = func.partition('(')
        args, _, return_ = other.partition(')')
        funcname = funcname.strip().removeprefix('pub fn').strip()
        args_type = [i.partition(':')[2].strip() for i in args.split(', ')]
        return_type = return_.partition('->')[2].strip().partition('{')[0].strip()
        content = self.content
        lines = content.split('\n')
        inputs = [i for i in lines if '<strong>Input:</strong>' in i]
        outputs = [i for i in lines if '<strong>Output:</strong>' in i]
        outputs += [''] * (len(inputs) - len(outputs))
        result = []
        cases = []
        for i, o in zip(inputs, outputs):
            i = html.unescape(i.replace('<strong>Input:</strong>', ''))
            o = html.unescape(o.replace('<strong>Output:</strong>', ''))
            args = i.split(', ')
            transed = [trans_arg(arg, type) for arg, type in zip(args, args_type)]
            cases.append((f"{','.join(transed)}", trans_arg(o, return_type, True)))
        if multi:
            origin_func_args = '(' + func.partition('(')[2].partition('{')[0]
            result.append(f"fn test(func: fn{origin_func_args}) {{")
            for func_in, func_out in cases:
                if unorder:
                    result.append(f"assert_eq!(unorder(func({func_in})), unorder({func_out}));")
                else:
                    result.append(f"assert_eq!(func({func_in}), {func_out});")
            result.append("}")
            result.append(f"test({funcname});")
        else:
            for func_in, func_out in cases:
                if unorder:
                    result.append(f"assert_eq!(unorder({funcname}({func_in})), unorder({func_out}));")
                else:
                    result.append(f"assert_eq!({funcname}({func_in}), {func_out});")
        return result


def get_problems(keyword='', skip=0, limit=50):
    url = "https://leetcode-cn.com/graphql"
    query = """
    query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
      problemsetQuestionList(
        categorySlug: $categorySlug
        limit: $limit
        skip: $skip
        filters: $filters
      ) {
        hasMore
        total
        questions {
          acRate
          difficulty
          freqBar
          frontendQuestionId
          isFavor
          paidOnly
          solutionNum
          status
          title
          titleCn
          titleSlug
        }
      }
    }

    """
    payload = {
        "query": query,
        "variables": {"categorySlug": "", "skip": skip, "limit": limit, "filters": {}}
    }
    if keyword:
        payload['variables']['filters']["searchKeywords"] = str(keyword)
    rsp = requests.post(url, json=payload)
    data = rsp.json()['data']['problemsetQuestionList']['questions']
    problem = [Problem(i) for i in data]
    return {i.id: i for i in problem}


BASE_DIR = os.path.dirname(os.path.realpath(__file__))


@click.group()
def cli():
    """generate leetcode rust problem file"""


@cli.command()
@click.option('-f', '--force', is_flag=True)
@click.option('-s', '--slug', is_flag=True)
@click.option('-m', '--multi', is_flag=True)
@click.option('-u', '--unorder', is_flag=True)
@click.argument('pid')
def get(pid, force, multi, slug, unorder):
    pid = pid.strip()
    path = ''
    if slug:
        slug = pid
    else:
        path = os.path.join(BASE_DIR, "src", "bin", f"leetcode_{pid}.rs")
        if os.path.exists(path):
            if not force:
                logger.error(f"path {path} exist")
                return
            else:
                logger.warning(f"will replace {path}")
        problems = get_problems(pid)
        problem = problems[str(pid)]
        slug = problem.key
    detail = get_problem_detail(slug)
    if not detail:
        logger.warning("get empty problem detail")
        return
    if path == '':
        path = os.path.join(BASE_DIR, "src", "bin", f"leetcode_{detail.id}.rs")
        if os.path.exists(path):
            if not force:
                logger.error(f"path {path} exist")
                return
            else:
                logger.warning(f"will replace {path}")
    with open(path, "w", encoding='utf-8') as f:
        cases = ""
        try:
            cases = detail.rust_testcase(multi, unorder)
        except Exception as e:
            logger.error(f"generate testcases fail: {e}")
        f.write(f"//! {detail.ch_title}\n")
        f.write("\n")
        f.write(detail.rust_template('\n'.join(cases)))
        f.write("\n")
        f.write("\n")
        f.write("fn main() {\n")
        f.write('\n'.join(cases))
        f.write('\n')
        f.write('}\n')
    print(path)
    subprocess.run(f'git add {path}', shell=True)


@cli.command('range')
@click.argument('start')
@click.argument('end')
def range_(start, end):
    start, end = int(start), int(end)
    problems = get_problems(skip=start - 1, limit=100)
    filtered = [int(id) for id in problems if id.isnumeric() and start <= int(id) <= end]
    for id in filtered:
        try:
            get.callback(str(id), False, True, '', False)
        except Exception as e:
            logger.error(f"get {id} fail: {e}")


@cli.command()
def fix_id():
    for file in glob.glob("src/bin/leetcode_*.rs"):
        pid = file.partition('_')[2].partition('.')[0]
        if not pid.isdigit():
            continue
        pid = int(pid)
        if pid < 5000:
            continue
        with open(file, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            ch_title = first_line.strip('/! ').strip()
            problems = get_problems(ch_title)
            problems = [v for k, v in problems.items() if v.ch_title == ch_title]
            if problems:
                problem = problems[0]
                real_id = int(problem.id)
                if real_id != pid:
                    to = file.replace(str(pid), str(real_id))
                    print(f"rename {file} -> {to}")
                    os.rename(file, to)
                    subprocess.run(f'/usr/sbin/git add {to}', shell=True)


if __name__ == '__main__':
    cli()
