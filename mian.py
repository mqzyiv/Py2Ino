import ast
# i got lazy :/ 
builtin  =['abs','constrain','map','max','min','pow','sq','sqrt','bit','bitClear','bitRead','bitSet','bitWrite','highByte',
'lowByte',
'analogRead',
'analogReadResolution',
'analogReference',
'analogWrite',
'analogWriteResolution',
'cos',
'sin',
'tan',
'attachInterrupt',
'detachInterrupt',
'digitalPinToInterrupt',
'noTone',
'pulseIn',
'pulseInLong',
'shiftIn',
'shiftOut',
'tone',
'isAlphaNumeric',
'isAscii',
'isControl',
'isDigit',
'isGraph',
'isHexadecimalDigit',
'isLowerCase',
'isPrintable',
'isPunct',
'isSpace',
'isUpperCase',
'isWhitespace',
'interrupts',
'noInterrupts',
'delay',
'delayMicroseconds',
'micros',
'millis',
'random',
'randomSeed'
]
TYPE_MAP = {
    "int": "int",
    "float": "float",
    "str": "String",
    "bool": "bool"
}

class py2ino(ast.NodeVisitor):
  def __init__(self):
    self.functionnames = []
    self.variables = {}
    self.output = ""
    self.current_function = None
    self.function_returns = {}
  def get_op(self, op):
    if isinstance(op, ast.Add):
      return "+"
    elif isinstance(op, ast.Sub):
      return "-"
    elif isinstance(op, ast.Mult):
      return "*"
    elif isinstance(op, ast.Div):
      return "/"
    else:
      raise Exception(f"Unsupported operator: {type(op)}")
  def get_type(self, node):
    if isinstance(node, ast.Name):
        return TYPE_MAP.get(node.id, node.id)
    return "auto"  # fallback
  def infer_type(self, value):
    if isinstance(value, bool):
        return "bool"
    elif isinstance(value, float):
        return "float"
    elif isinstance(value, str):
        return "String"
    elif isinstance(value, int):
        return "int"
    else:
        return "auto"
  def visit_FunctionDef(self, node):
    self.functionnames.append(node.name)
    self.current_function = node.name
    args = []
    header = ""
    for arg in node.args.args:
        arg_name = arg.arg
        if arg.annotation:
            arg_type = self.get_type(arg.annotation)
        else:
            arg_type = "auto"  
        args.append(f"{arg_type} {arg_name}")
    header += ", ".join(args)
    retval = self.get_type(node.returns) if node.returns else "auto"
    self.function_returns[node.name] = set()
    old_output = self.output
    self.output = ""
    for i in node.body:
      self.visit(i)
    body_output = self.output
    self.output = old_output
    types = self.function_returns[node.name]
    if len(types) == 1:
        final_ret = list(types)[0]
    elif len(types) == 0:
        final_ret = "void"
    else:
        raise Exception(f"Inconsistent return types in {node.name}")
    self.output += f"{final_ret} {node.name}({header}) {{\n"
    self.output += body_output
    self.output+= '}\n'
  def valid_Pin(self,node):
      if isinstance(node.args[0],ast.Constant):
          if type(node.args[0].value) != int:
            raise Exception(f"pinMode function first argument must be an integer--line{node.lineno}")
          elif node.args[0].value not in range(14):
            raise ValueError(f"Input a valid pin number--line{node.lineno}")
          arg0 = node.args[0].value
      elif isinstance(node.args[0],ast.Name):
          if node.args[0].id not in self.variables:
            raise Exception(f"Undefined variable--line{node.lineno}")
          if self.variables[node.args[0].id]['type']!= "int":
            raise Exception(f"pinMode function first argument must be an integer--line{node.lineno}")
          elif self.variables[node.args[0].id]['expr'] not in range(14):
            raise ValueError(f"Input a valid pin number--line{node.lineno}")
          arg0 = node.args[0].id
      return arg0
  def visit_Assign(self, node):
   if isinstance(node.targets[0], ast.Name):
        target = node.targets[0].id
        expr = self.eval_expr(node.value)

        # infer type
        if isinstance(node.value, ast.Constant):
            var_type = self.infer_type(node.value.value)
        else:
            var_type = "auto"

        # emit
        if target in self.variables:
            self.output += f"{target} = {expr};\n"
        else:
            self.output += f"{var_type} {target} = {expr};\n"

        self.variables[target] = {
            "expr": expr,
            "type": var_type
        }
  def visit_If(self, node):
    cond = self.eval_expr(node.test)
    self.output += f"if ({cond}) {{\n"
    for stmt in node.body:
        self.visit(stmt)
    self.output += "}"
    if node.orelse:
        self.output += " else {\n"
        for stmt in node.orelse:
            self.visit(stmt)
        self.output += "}"
    self.output += "\n"
  def visit_Call(self, node):
    if isinstance(node.func, ast.Name):
      if node.func.id in builtin or node.func.id in self.functionnames:
        argarr = []
        for i in node.args:
          if isinstance(i,ast.Name):
            argarr.append(i.id)
          elif isinstance(i, ast.Constant):
            argarr.append(str(i.value))
        self.output+=f"{node.func.id}({','.join(argarr)});\n"
      elif node.func.id == 'pinMode':
        if len(node.args) != 2:
          raise Exception("pinMode function must have 2 arguments")
        arg1 = ""
        arg0 = ""
        #constante
        if isinstance(node.args[1],ast.Constant):
          if type(node.args[1].value)!= str or node.args[1].value not in ['OUTPUT', 'INPUT']:
            raise Exception(f"pinMode function second argument must be OUTPUT or INPUT--line{node.lineno}")
          arg1 = node.args[1].value

        #variabel
        elif isinstance(node.args[1],ast.Name):
          if node.args[1].id not in self.variables:
            raise Exception(f"Undefined variable--line{node.lineno}")
          if self.variables[node.args[1].id]['expr'] not in ['OUTPUT', 'INPUT']:
              raise Exception(f"pinMode function second argument must be OUTPUT or INPUT--line{node.lineno}")
          arg1 = self.variables[node.args[1].id]["expr"]
        #another one 
        arg0 = self.valid_Pin(node)
      
        self.output+= f'pinMode({arg0}, {arg1});\n'
      elif node.func.id == 'digitalWrite':
        if len(node.args) != 2:
          raise Exception("digitalWrite function must have 2 arguments")
        arg0 = self.valid_Pin(node)
        if isinstance(node.args[1],ast.Constant):
          if type(node.args[1].value)!= str or node.args[1].value not in ['HIGH', 'LOW']:
            raise Exception(f"digitalWrite function second argument must be HIGH or LOW--line{node.lineno}")
          arg1 = node.args[1].value

        #variabel
        elif isinstance(node.args[1],ast.Name):
          if node.args[1].id not in self.variables:
            raise Exception(f"Undefined variable--line{node.lineno}")
          if self.variables[node.args[1].id]["expr"] not in ['HIGH', 'LOW']:
              raise Exception(f"pinMode function second argument must be HIGH or LOW--line{node.lineno}")
          arg1 = self.variables[node.args[1].id]["expr"]
        self.output+= f"digitalWrite({arg0}, {arg1});\n"
      else:
        raise Exception(f'Function not defined--line{node.lineno}')
  def visit_Return(self, node):
    if isinstance(node.value, ast.Constant):
        self.output += f"return {node.value.value};\n"
        if self.current_function:
          self.function_returns[self.current_function].add(self.infer_type(node.value.value))
    elif isinstance(node.value, ast.Name):
        self.output += f"return {node.value.id};\n"
        val = self.variables.get(node.value.id)
        if val is not None:
            self.function_returns[self.current_function].add(val["type"])
  def eval_expr(self, node):
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return "true" if node.value else "false"
        return str(node.value)
    elif isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.BinOp):
        left = self.eval_expr(node.left)
        right = self.eval_expr(node.right)
        op = self.get_op(node.op)
        return f"({left} {op} {right})"


def start(tree):
  visitfun = py2ino()
  visitfun.visit(tree)
  if 'setup' not in visitfun.functionnames:
    raise Exception("setup function not found")
  if 'loop' not in visitfun.functionnames:
    raise Exception("loop function not found")
  return visitfun.output
tree = ast.parse(open('blink.txt','r').read())
o = start(tree)
print(o)
# if len(sys.argv) < 2:
#   print('provide an input file')
#   exit(0)
# input_file = sys.argv[1] 
# orig_stdout = sys.stdout
# result = subprocess.run(["mkdir", input_file[:-3]])
# out = open(input_file[:-3]+'/'+input_file[:-2]+'ino', 'w')
# sys.stdout = out
# f = open(input_file, 'r').read()
# tree = ast.parse(f)
# start(tree)
# sys.stdout = orig_stdout
# out.close()
# if len(sys.argv) >=3:
#   if sys.argv[2] == 'c':
#     pass