"""直接测试run.py"""
import sys
sys.path.insert(0, r'C:\Users\Administrator\.workbuddy\distill-system')
sys.argv = ['run.py', 'search', '普通人']
from run import main
main()
