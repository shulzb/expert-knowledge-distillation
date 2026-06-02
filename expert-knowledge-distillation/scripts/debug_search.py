"""Debug run.py search"""
import sys
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')

print(f'sys.argv: {sys.argv}')
print(f'args[2:]: {sys.argv[2:]}')

cmd = sys.argv[1]
args = sys.argv[2:]

from query.cmd_query import cmd_search
class FakeArgs:
    query = args
    limit = 3
    semantic = False

q = ' '.join(args)
print(f'query: {repr(q)}')

from db.database import fts_search
r = fts_search(q, 3)
print(f'results: {len(r)}')
