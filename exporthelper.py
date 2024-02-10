import ast

EXPORT_HELPER_NAME = "__generated_helper_export__"
# derived from https://github.com/Infinidat/munch
# Used to make the locals() dictionary into a attribute-accessible module
EXPORT_HELPER_CONTENTS = f"""
class {EXPORT_HELPER_NAME}(dict):
	C=KeyError
	A=AttributeError
	def __init__(A,C):A.update(**C)
	def __getattr__(B,k):
		try:return object.__getattribute__(B,k)
		except A:
			try:return B[k]
			except C:raise A(k)
	def __setattr__(B,k,v):
		try:object.__getattribute__(B,k)
		except A:
			try:B[k]=v
			except:raise A(k)
		else:object.__setattr__(B,k,v)
	def __delattr__(B,k):
		try:object.__getattribute__(B,k)
		except A:
			try:del B[k]
			except C:raise A(k)
		else:object.__delattr__(B,k)
"""


def get_export_helper():
    return ast.parse(EXPORT_HELPER_CONTENTS, mode="exec").body[0]
