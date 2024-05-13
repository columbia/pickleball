/*
 * Usage: ./joern --script ./reduce.sc --param inputPath=<path to python project source> --param modelClass=SequenceTagger
 */

import io.shiftleft.codepropertygraph.generated.nodes.{ Call => CallNode }
import scala.collection.mutable.ListBuffer
import scala.None
import scala.Some

case class ReduceCallable(
  classDecl: Option[TypeDecl],
  callable: Option[Method],
  retloc: String
)

def addCallablesForRetVal(ret: Return, pclass: TypeDecl, callables: ListBuffer[ReduceCallable]) : Boolean = {

  val retloc = ret.method.filename + ":" + ret.lineNumber.getOrElse(-1)
  val reduce_args_retvals = ret.argumentOut.l
  if (reduce_args_retvals.length == 0) {
    println("Unknown reduce return value for " + ret + " at " + retloc)
    callables += ReduceCallable(None, None, retloc)
    return false
  }

  val reduce_args_ret = reduce_args_retvals.l(0)

  var callable_name = ""
  for (arg <- reduce_args_ret) {
    if (arg.isLiteral && arg.asInstanceOf[Literal].typeFullName == "__builtin.str") {
      callable_name = arg.asInstanceOf[Literal].code.replace("\"", "")
    } else if (arg.isCall) {
      val call = arg.asInstanceOf[CallNode]
      if (call.methodFullName == "<operator>.tupleLiteral") {
        val arg0 = call.argument.l(0)
        if (arg0.isIdentifier) {
          callable_name = arg0.asInstanceOf[Identifier].name
        } else if (arg0.isCall) {
          // FIXME this can happen in cases where the callable is accessed through a module
          // and Joern sees it as a fieldIdentifier
          val arg0_call = arg0.asInstanceOf[CallNode]
          if (arg0_call.name == "<operator>.fieldAccess") {
            // FIXME
            callable_name = arg0.asInstanceOf[CallNode].name
          } else {
            throw new Exception("Unknown call for reduce return value " + arg0)
          }
        } else {
          throw new Exception("Unknown first argument " + arg0 + " to reduce tuple " + arg)
        }
      } else {
        // Follow this other call to get its return values
        val returns = cpg.ret.filter(x => x.method.name == call.name)
        for (new_ret <- returns) {
          return addCallablesForRetVal(new_ret, pclass, callables)
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
    val matching_callables = cpg.method.filter(_.name == callable_name).l
    if (matching_callables.length == 0) {
      callables += ReduceCallable(None, None, retloc)
      return false
    }
    val callable = matching_callables.l(0)
    callables += ReduceCallable(Some(pclass), Some(callable), retloc)
  }

  true
}


@main def main(inputPath: String) = {

  importCode(inputPath)

  var callables = new ListBuffer[ReduceCallable]()
  val reduce_rets = cpg.ret.l.filter(_.method.name.matches("__reduce_ex__|__reduce__"))

  for (reduce_ret <- reduce_rets) {
    println("Analyzing ret " + reduce_ret + " at " + reduce_ret.method.filename + ":" + reduce_ret.lineNumber.getOrElse(-1))
    // Pass the correct class type here so it's not lost if addCallablesForRetVal recurses
    var pclass = reduce_ret.method.typeDecl.l(0)
    addCallablesForRetVal(reduce_ret, pclass, callables)
  }

  for (matching_callable <- callables) {
    matching_callable.callable match {
      case Some(callable) => {
        val classDecl = matching_callable.classDecl.get
        println(classDecl.name + " " + callable.name + " " + matching_callable.retloc)
      }
      case None => {
        println("No match found for callable at " + matching_callable.retloc)
      }
    }
  }

}
