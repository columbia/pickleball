/*
 * Usage: ./joern --script ./analyze.sc --param inputPath=<path to python project cpg> --param modelClass=SequenceTagger
 */

import scala.collection.mutable
import io.shiftleft.codepropertygraph.generated.nodes.{
  Return, TypeDecl, Method, Identifier, FieldIdentifier, Literal, Call => CallNode }

val PyModuleSuffix = ".py:<module>."
val ModuleSuffix = ":<module>."

def attributeTypes(className: String): Iterator[String] = {
  /* TODO: Handle types stored in collections */
  cpg.typeDecl.fullName(className).member.flatMap {
    member =>
      (member.typeFullName +: member.dynamicTypeHintFullName)
        .filterNot(_.matches("object|ANY"))
        .filterNot(isPrimitiveType(_))
        .filterNot(_.endsWith(".__init__"))
        .distinct
  }
}

def subClasses(parentClass: String): Iterator[String] = {
  cpg.typeDecl
    // Filter will identify any type full names that end in .parentClass. This
    // will not match exactly on the full name, so there may be type collisions
    // in the project. The query may also be expensive.
    .filter(_.inheritsFromTypeFullName.exists(_.split('.').lastOption == Some(parentClass)))
    .name
    .filterNot(_.matches("object|ANY"))
    .filterNot(x => x.contains("<body>") || x.contains("<fakeNew>") || x.contains("<meta"))
}

def superClasses(className: String): Iterator[String] = {
  cpg.typeDecl
    .fullName(className)
    //.inheritsFromTypeFullName
    .baseType.typeDeclFullName
    .filterNot(_.matches("object|ANY"))
    .filterNot(x => x.contains("<body>") || x.contains("<fakeNew>") || x.contains("<meta"))
}

case class ReduceCallable(
  classDecl:  Option[TypeDecl],
  callable:   Option[Method],
  retloc:     String
)

// val reduceReturns = cpg.ret.filter(_.method.name.matches("_reduce_ex__|__reduce__"))

def constructReduceCallables(callableName: String, classDecl: TypeDecl, retLoc: String): Set[ReduceCallable] = {
  cpg.method.filter(_.fullName == callableName).l match {
    case Nil => Set()
    case callables => callables.map(callable =>
      println(s"- constructing callable for ${classDecl.name}:${callable.name}")
      ReduceCallable(Some(classDecl), Some(callable), retLoc)).toSet
  }
}

/*
 * Given a return statement in a __reduce__ or __reduce_ex__ method, determine
 * the returned callable object. Also takes the typeDecl of the class that
 * implements the __reduce__ method.
 *
 * TODO: I think that the types also contained in the tuples need to be checked
 * as well.
 */
def callablesFromReduceReturn(ret: Return, pclass: TypeDecl): Set[ReduceCallable] = {
  val retLoc = s"${ret.method.filename}:${ret.lineNumber.getOrElse(-1)}"

  /*
   * The return value of a reduce call can either be: a string literal, a tuple,
   * or an expression that we need to recursively descend into.
   */
  ret.argumentOut.l match {
    case retVal :: _ =>
      retVal match {
        case literal: Literal if literal.typeFullName == "__builtin.str" =>
          /* Handle string literal */
          println(s"- string literal: ${literal.code.replace("\"", "")}")
          constructReduceCallables(literal.code.replace("\"", ""), pclass, retLoc)
        case call: CallNode if call.methodFullName == "<operator>.tupleLiteral" =>
          /* Handle tuple return value */
          println(s"- tuple: ${call.name}")
          call.argument.l match {
            case Nil => Set()
            case (arg0: Identifier) :: _ =>
              /* Argument is a method name defined in the same file. Add the correct module full name prefix */
              val callableName = s"${call.method.filename}${ModuleSuffix}${arg0.name}"
              println(s"- callable name: ${callableName}")
              constructReduceCallables(callableName, pclass, retLoc)
            case (arg0: CallNode) :: _ if arg0.name == "<operator>.fieldAccess" =>
              /* Argument is a */
              /* TODO: Refactor functionally */
              var faccess = arg0
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
                /* FIXME */
              }
              constructReduceCallables(fullName, pclass, retLoc)
            case (arg0: CallNode) :: _ => /* Error */
              println(s"Unknown call for reduce return value ${arg0.name}")
              Set()
          }
        case call: CallNode =>
          /* Handle expression  by recursively descending to get return values */
          println(s"- call: ${call.name}")
          val returns = cpg.ret.filter(_.method.name == call.name)
          returns.flatMap {newRet => callablesFromReduceReturn(newRet, pclass) }.toSet
        case _ =>
          println(s"Unknown reduce return value @ ${retLoc}")
          Set(ReduceCallable(None, None, retLoc))
      }
    case Nil =>
      println(s"Unknown reduce return value for ${ret} @ ${retLoc}")
      Set(ReduceCallable(None, None, retLoc))
  }
}

/* Given a class name, return all the callables that the class __reduce__|__reduce_ex__
 * method returns, if it exists.
 */
def reduces(classFullName: String): Iterator[ReduceCallable] = {

  val reduceReturns = cpg.ret.filter(_.method.name.matches("__reduce_ex__|__reduce__"))
  val classReduceReturns: Iterator[Return] = reduceReturns.filter(_.method.typeDecl.head.name == classFullName)

  classReduceReturns.flatMap { ret =>
    println(s"Analyzing return statement ${ret} @ ${ret.method.filename}:${ret.lineNumber.getOrElse(-1)}")
    val pclass = ret.method.typeDecl.head   // may nead headOption - occurs if the __reduce__ method is not in a class, which shouldn't be the case
    callablesFromReduceReturn(ret, pclass)
  }
}

def isPrimitiveType(className: String) : Boolean = className.startsWith("__builtin.")

class UniqueQueue[T] extends mutable.Queue[T] {

  val seen: mutable.Set[T] = mutable.Set.empty[T]

  override def enqueue(obj: T): UniqueQueue.this.type = {
    if (!seen(obj)) {
      seen.add(obj)
      super.enqueue(obj)
    } else {
      this
    }
  }

}

def inferTypeFootprint(modelClass: String): (mutable.Set[String], mutable.Set[String]) = {

  val allowedGlobals: mutable.Set[String] = mutable.Set()
  val allowedReduces: mutable.Set[String] = mutable.Set()

  val queue: UniqueQueue[String] = UniqueQueue()
  queue.enqueue(modelClass)

  while (!queue.isEmpty) {

    val targetClass = queue.dequeue
    println(s"analyzing: ${targetClass}")
    val targetTypeDecls = cpg.typeDecl.fullName(targetClass).toList

    if (targetTypeDecls.isEmpty) {
      println(s"- !! unable to find typeDecl for class ${targetClass} !!")
      val fullNames = cpg.typeDecl(targetClass).fullName.l
      println(s"-- found typeDecls with names: ${fullNames.mkString(",")}")
    }

    val reduceMethods = reduces(targetClass)
    if (reduceMethods.nonEmpty) {
      println(s"- reduce method identified")
      reduceMethods.foreach { r =>
        println(s"- adding callables: ${r.callable.fullName.mkString(",")}")
        allowedReduces ++= r.callable.fullName.toSet
      }

      // TODO: Analyze all types of arguments to reduceMethods

    } else {
      println(s"- no reduce method identified")
      allowedGlobals.add(targetClass)

      // TODO: Distinguish class constructor and add it to allowed callables

      // TODO: Analyze all types of arguments to constructor

      /** Analyze all subclasses of targetClass */
      println(s"- sub classes: ${subClasses(targetClass).toList.mkString(",")}")
      subClasses(targetClass).foreach(queue.enqueue)

      /** Approximate all types that can be written to attributes of the targetClass
       * analyzing all class attribute types. */
      println(s"- attribute types: ${attributeTypes(targetClass).toList.mkString(",")}")
      attributeTypes(targetClass)
        .filterNot(isPrimitiveType)
        .foreach(queue.enqueue)

      /* Ensure that attribute types of parent classes are also collected */
      val parentAttributes = superClasses(targetClass).flatMap(attributeTypes).toList
      println(s"- parent class attribute types: ${parentAttributes.mkString(",")}")
      parentAttributes
        .filterNot(isPrimitiveType)
        .foreach(queue.enqueue)
    }
  }

  (allowedGlobals, allowedReduces)
}

@main def main(inputPath: String, modelClass: String) = {

  importCpg(inputPath)

  val (allowedGlobals, allowedReduces) = inferTypeFootprint(modelClass)

  println()
  println(s"Allowed Globals: \n- ${allowedGlobals.mkString("\n- ")}")
  println(s"Allowed Reduces: \n- ${allowedReduces.mkString("\n- ")}")
}
