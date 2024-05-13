/*
 * Usage: ./joern --script ./reduce.sc --param inputPath=<path to python project source> --param modelClass=SequenceTagger
 */

import io.shiftleft.codepropertygraph.generated.nodes.{ Call => CallNode }
import scala.collection.mutable.ListBuffer

case class MemberType(
  name: String,
  types: IndexedSeq[String] = IndexedSeq.empty
)

def addCallablesForRetVal(ret: Return, callables: ListBuffer[Map[TypeDecl, Method]]) : Boolean = {

  val reduce_args = ret.map(x => x.argumentOut.l(0))
  val pclass = ret.method.typeDecl.l(0)

  var callable_name = ""
  for (arg <- reduce_args) {
    if (arg.isLiteral && arg.asInstanceOf[Literal].typeFullName == "__builtin.str") {
      callable_name = arg.asInstanceOf[Literal].code.replace("\"", "")
    } else if (arg.isCall) {
      val call = arg.asInstanceOf[CallNode]
      if (call.methodFullName == "<operator>.tupleLiteral") {
        val arg0 = call.argument.l(0)
        if (arg0.isIdentifier) {
          callable_name = arg0.asInstanceOf[Identifier].name
        } else {
          throw new Exception("Unknown first argument to reduce tuple: " + arg0)
        }
      } else {
        // Follow this other call to get its return values
        val returns = cpg.ret.filter(x => x.method.name == call.name)
        for (new_ret <- returns) {
          return addCallablesForRetVal(new_ret, callables)
        }
      }
    } else {
      throw new Exception("Unknown reduce return value: " + arg)
    }
    // TODO will probably have to match the callable to the proper module, e.g., from
    // pickle docs:
    // If a string is returned, the string should be interpreted as the name of
    // a global variable. It should be the object’s local name relative to its
    // module; the pickle module searches the module namespace to determine the
    // object’s module. This behaviour is typically useful for singletons.
    val callable = cpg.method.filter(_.name == callable_name).l(0)
    callables += Map(pclass -> callable)
  }

  true
}


@main def main(inputPath: String) = {

  importCode(inputPath)

  var callables = new ListBuffer[Map[TypeDecl, Method]]()
  val reduce_rets = cpg.ret.l.filter(_.method.name.matches("__reduce_ex__|__reduce__"))

  for (reduce_ret <- reduce_rets) {
    addCallablesForRetVal(reduce_ret, callables)
  }

  for (pair <- callables) {
    for ((pclass, callable) <- pair) {
      println(pclass.name + " " + callable.name)
    }
  }

}
