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

val PyModuleSuffix = ".py:<module>."
val ModuleSuffix = ":<module>."

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
          // This should correspond to a method that's defined in the same file,
          // so just prefix it with the name of the current module
          callable_name = call.method.filename + ModuleSuffix + arg0.asInstanceOf[Identifier].name
        } else if (arg0.isCall) {
          val arg0_call = arg0.asInstanceOf[CallNode]
          // This can happen in cases where the callable is accessed through a module
          // (i.e., a different file) and Joern sees it as a fieldIdentifier
          if (arg0_call.name == "<operator>.fieldAccess") {
            var faccess = arg0_call
            var faccess_arg0 = faccess.asInstanceOf[CallNode].argument.l(0)
            var faccess_fident = faccess.asInstanceOf[CallNode].argument.l(1).asInstanceOf[FieldIdentifier]
            var fullName = faccess_fident.canonicalName
            while (faccess_arg0.isCall && faccess_arg0.asInstanceOf[CallNode].name == "<operator>.fieldAccess") {
              faccess = faccess_arg0.asInstanceOf[CallNode]
              faccess_arg0 = faccess.argument.l(0)
              faccess_fident = faccess.asInstanceOf[CallNode].argument.l(1).asInstanceOf[FieldIdentifier]
              fullName = faccess_fident.canonicalName + PyModuleSuffix + fullName
            }
            if (faccess_arg0.isIdentifier) {
              // FIXME Here we actually need to see how the top-level identifier
              // was imported and deduce what the actual full name of the callable
              // would look like in Joern
              // FIXME If this is a variable, we need to follow it (something similar
              // to QUACK) and try to figure out its value

            }
            callable_name = fullName
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
      println("Unknown reduce return value: " + arg + " (" + retloc + ")")
      callables += ReduceCallable(None, None, retloc)
      return false
    }
    // TODO will probably have to match the callable to the proper module, e.g., from
    // pickle docs:
    // If a string is returned, the string should be interpreted as the name of
    // a global variable. It should be the object’s local name relative to its
    // module; the pickle module searches the module namespace to determine the
    // object’s module. This behaviour is typically useful for singletons.
    val matching_callables = cpg.method.filter(_.fullName == callable_name).l
    if (matching_callables.length == 0) {
      callables += ReduceCallable(None, None, retloc)
      return false
    }
    val callable = matching_callables.l(0)
    callables += ReduceCallable(Some(pclass), Some(callable), retloc)
  }

  true
}


@main def main(inputCpg: String, focus_class: String = "") = {

  importCpg(inputCpg)

  var callables = new ListBuffer[ReduceCallable]()
  var reduce_rets = cpg.ret.l.filter(_.method.name.matches("__reduce_ex__|__reduce__"))
  if (focus_class != "") {
    reduce_rets = reduce_rets.filter(_.method.typeDecl.l(0).name == focus_class)
  }

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
        println(classDecl.name + " " + callable.name + " " + matching_callable.retloc + " (" + callable + ")")
      }
      case None => {
        println("No match found for callable at " + matching_callable.retloc)
      }
    }
  }

}
