import ast

class py2ino(ast.NodeVisitor):
  def __init__(self):
    self.functionnames = []
    self.variables = {}
  def get_type(self, node):
    if isinstance(node, ast.Name):
        return node.id
    return "auto"  # fallback
  def visit_FunctionDef(self, node):
    self.functionnames.append(node.name)
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
    if (node.returns):
      retval = self.get_type(node.returns)
      print(f'{retval} {node.name} ({header}) {{')
    else:
      print(f'void {node.name}({header}) {{')
    for i in node.body:
      self.visit(i)
    print('}')
  def valid_Pin(self,node):
      if isinstance(node.args[0],ast.Constant):
          if type(node.args[0].value) != int:
            raise Exception(f"pinMode function first argument must be an integer--line{node.lineno}")
          elif node.args[0].value not in range(14):
            raise ValueError(f"Input a valid pin number--line{node.lineno}")
          arg0 = node.args[0].value
      elif isinstance(node.args[0],ast.Name):
          if type(self.variables[node.args[0].id] ) != int:
            raise Exception(f"pinMode function first argument must be an integer--line{node.lineno}")
          elif self.variables[node.args[0].id] not in range(14):
            raise ValueError(f"Input a valid pin number--line{node.lineno}")
          arg0 = node.args[0].id
      return arg0
  def visit_Assign(self, node):
    if isinstance(node.targets[0], ast.Name):
      value = ""
      if isinstance(node.value,ast.Constant):
        value = node.value.value
      elif isinstance(node.value,ast.Name):
        value = self.variables[node.value.id]
      if node.targets[0].id in self.variables:
        self.variables[node.targets[0].id] = value
        print("#check that the types match")
        print(f"{node.targets[0].id} = {value};")
      else:
        print(f"{type(value).__name__} {node.targets[0].id} = {value};")
        self.variables[node.targets[0].id] = value
    

  def visit_Call(self, node):
    if isinstance(node.func, ast.Name):
      if node.func.id == 'pinMode':
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
          if self.variables[node.args[1].id] not in ['OUTPUT', 'INPUT']:
              raise Exception(f"pinMode function second argument must be OUTPUT or INPUT--line{node.lineno}")
          arg1 = self.variables[node.args[1].id]  
        #another one 
        arg0 = self.valid_Pin(node)
      
        print(f'pinMode({arg0}, {arg1});')
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
          if self.variables[node.args[1].id] not in ['HIGH', 'LOW']:
              raise Exception(f"pinMode function second argument must be HIGH or LOW--line{node.lineno}")
          arg1 = self.variables[node.args[1].id]
        print(f"digitalWrite({arg0}, {arg1});")
      


def start(tree):
  visitfun = py2ino()
  visitfun.visit(tree)
  if 'setup' not in visitfun.functionnames:
    raise Exception("setup function not found")
  if 'loop' not in visitfun.functionnames:
    raise Exception("loop function not found")
    