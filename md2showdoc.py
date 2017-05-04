# -*- coding:utf-8 -*-
import sys
import urllib
import json

def module_dict():
    return sys.modules[__name__]

MODULE_DICT = module_dict()

DEFINTIONS = {}


class APIDocument(object):
    method = None
    def __init__(self, root, path):
        self.path = path
        self.root = root
        self.desc = ""

    def parse(self):
        descr= self.root.get("description") if "description" in self.root else self.root.get("summary")
        step = [
            str(DescrNode(descr)),
            str(PathNode(self.path)),
            str(HttpMethodNode(self.method)),
            str(ParamNode(self.root.get("parameters", []))),
            str(ResponseNode()),
            str(RespParamNode(self.root))
        ]
        return "".join(step)

    def __str__(self):
        return self.parse()

class GETAPIDocument(APIDocument): 
    method = "GET"

class POSTAPIDocument(APIDocument):
    method = "POST"

class APINode(object): 
    def __init__(self, name):
        self.name = name
        self.value = ""

    def __str__(self):
        return ""

class DescrNode(APINode):
    def __init__(self, name):
        self.name = name
        super(DescrNode, self).__init__(name)

    def __str__(self):
        return "\n**简要描述：**\n- %s\n\n" % self.name.encode("utf-8")
   
class PathNode(APINode):
    def __init__(self, name):
        self.name = name
        super(PathNode, self).__init__(name)

    def __str__(self):
        return "\n**请求URL：**\n- `%s`\n\n" % self.name.encode("utf-8")       
 
class HttpMethodNode(APINode):
    def __init__(self, name):
        self.name = name
        super(HttpMethodNode, self).__init__(name)

    def __str__(self):
        return "\n**请求方式：**\n- %s\n\n" % self.name.encode("utf-8")      

class ParamNode(APINode):
    def __init__(self, params):
        self.params = params
        super(ParamNode, self).__init__(params)
        self.paramNode = ["\n**参数：**\n\n"]
        self.paramNode.append("|".join(["|参数名", "请求方式","必选", "类型", "说明|默认值|"]))
        self.paramNode.append("|:----|:---|:---|:-----|:----|-----|")

    def parse(self):
        tpl = "|%s|%s|%s|%s|%s|%s|"
        for param in self.params:
            name = str(param.get("name"))
            inMethod = param.get("in")
            paramMethod = str("json" if inMethod == "body" else inMethod)
            required = str("是" if param.get("required") else "否")
            dataType = param.get("type") if "type" in param else param.get("schema")

            if "schema" in param and ("type" in dataType and dataType.get("type") == "array"):
                schemaName = param.get("schema")["items"]["$ref"].split("/")[2]
                dataType = str("[[%s](#%s)]" % (schemaName, schemaName))
            elif "schema" in param and ("type" not in dataType):
                schemaName = dataType.get("$ref").split("/")[2]
                dataType = str("[%s](#%s)" % (schemaName, schemaName))
            else:
                dataType = str(dataType)
            
            descr = str(param.get("description",u"无").encode("utf-8"))
            default = str(param.get("default") if "default" in param else "")
            self.paramNode.append(tpl % (name, paramMethod, required, dataType, descr, default))
        return "\n".join(self.paramNode)

    def __str__(self):
        return self.parse()
 

class ResponseNode(APINode):
    def __init__(self):
        super(ResponseNode, self).__init__(None)

    def __str__(self):
        return """
\n\n**返回示例**

```
{
    "code": "200",
    "message": "一些描述",
    "desc": "业务描述"
    "data": {}
}
```
\n\n
"""

class RespParamNode(APINode):
    def __init__(self, root):
        self.root = root
        super(RespParamNode, self).__init__(root)

    def __str__(self):
        return """
\n
**返回参数说明** 
\n
|参数名|必选|类型|说明|
|:----|:---|:-----|-----|
|name | 是 | string| 名字|
\n
**备注** 
- 更多返回错误代码请看首页的错误代码描述
\n\n
        """       

class DefinitionNode(APINode):
    def __init__(self):
        super(DefinitionNode, self).__init__(None)

    def parser(self):
        tpl = "|%s|%s|%s|%s|"
        ParamNode = []
        for name,body in DEFINTIONS.iteritems():
            title = str("\n#" + name + "\n\n")
            header = "|".join(["|参数名", "必选", "类型", "说明|"])
            headerline = "|:----|:---|:-----|-----|"
            ParamNode.extend([title, header, headerline])
            body = body.get("properties")
            requireds = body.get("required", [])
            for field, value in body.iteritems():
                paramName = str(field)
                required = str("是" if paramName in requireds else "否")
                dataType = str(value.get("type"))
                descr = str(value.get("description", " ").encode("utf-8"))
                if dataType == "array":
                    dataType = str("[" + value.get("items").get("type") + "]")
                ParamNode.append(tpl % (paramName, required, dataType, descr))

        return "\n".join(ParamNode)

    def __str__(self):
        return self.parser()

def main():
    url = sys.argv[1]
    apibody = json.loads(urllib.urlopen(url).read())
    if "definitions" in apibody:
        global DEFINTIONS
        DEFINTIONS = apibody.get("definitions")

    showdocBody = []
    for path, apiDescr in apibody["paths"].iteritems():
        for method in apiDescr:
            methodName = method.upper() + "APIDocument"
            processor = getattr(MODULE_DICT, methodName)(apiDescr[method], path)
            showdocBody.append(str(processor))
        
    showdocBody.append(str(DefinitionNode()))
    print("\n".join(showdocBody))

if __name__ == '__main__':
    main()
