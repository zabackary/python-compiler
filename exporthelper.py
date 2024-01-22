import ast

EXPORT_HELPER_NAME = "__generated_helper_export__"


def get_export_helper():
    return ast.ClassDef(
        name=EXPORT_HELPER_NAME,
        bases=[],
        keywords=[],
        body=[
            ast.FunctionDef(
                name='__init__',
                args=ast.arguments(
                    posonlyargs=[],
                    args=[
                        ast.arg(arg='self'),
                        ast.arg(arg='entries')
                    ],
                    kwonlyargs=[],
                    kw_defaults=[],
                    defaults=[]
                ),
                body=[
                    ast.Expr(
                        value=ast.Call(
                            func=ast.Attribute(
                                value=ast.Attribute(value=ast.Name(
                                    id='self', ctx=ast.Load()), attr='__dict__', ctx=ast.Load()),
                                attr='update',
                                ctx=ast.Load()),
                            args=[
                                ast.Name(id='entries', ctx=ast.Load())
                            ],
                            keywords=[]
                        )
                    )
                ],
                decorator_list=[]
            )
        ],
        decorator_list=[]
    )
