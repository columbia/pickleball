/*
 * Usage: ./joern --script ./analyze.sc --param inputPath=<path to python project cpg> --param modelClass=SequenceTagger --param outputPath=<path to output>
 */

import scala.collection.mutable
import io.shiftleft.codepropertygraph.generated.nodes.{
  Return, TypeDecl, Method, Identifier, FieldIdentifier, Literal, Call => CallNode }

val PyModuleSuffix = ".py:<module>."
val ModuleSuffix = ":<module>."
val CollectionPrefix ="__collection."

def attributeTypes(className: String): Iterator[String] = {
  /* TODO: Handle types stored in collections */
  cpg.typeDecl.fullName(className).member.flatMap {
    member =>
      (member.typeFullName +: member.dynamicTypeHintFullName)
        .filterNot(_.matches("object|ANY"))
        .filterNot(isPrimitiveType(_))
        /*  Constructors assigned to attributes may result in types of
         *  Class.__init__ or Class.__init__.<returnValue>. When these are
         *  seen, we can strip the suffix and just add the class name to the
         *  analysis Queue.
         * */
        .map { memberType =>
          memberType match {
            case s if s.endsWith(".__init__.<returnValue>") => s.stripSuffix(".__init__.<returnValue>")
            case s if s.endsWith(".__init__") => s.stripSuffix(".__init__")
            case _ => memberType
          }
        }
        .distinct
  }
}

def subClasses(parentClass: String): Iterator[String] = {
  /* Identify all type declarations that inherit from the parentClass */
  cpg.typeDecl
    .filter(_.inheritsFromTypeFullName.contains(parentClass))
    .fullName
    .filterNot(_.matches("object|ANY"))
    .filterNot(x => x.contains("<body>") || x.contains("<fakeNew>") || x.contains("<meta"))
}

def superClasses(className: String): Iterator[String] = {
 /**
 * Sometimes type information is in both the inheritsFromTypeFullName and the
 * baseType fields (or one, and not the other). We try searching for both.
 */
 cpg.typeDecl
    .fullName(className)
    //.inheritsFromTypeFullName
    .baseType.typeDeclFullName
    .filterNot(_.matches("object|ANY"))
    .filterNot(x => x.contains("<body>") || x.contains("<fakeNew>") || x.contains("<meta"))
    .map(stripTypeVar)
  ++
  cpg.typeDecl
    .fullName(className)
    .inheritsFromTypeFullName
    .filterNot(_.matches("object|ANY"))
    .filterNot(x => x.contains("<body>") || x.contains("<fakeNew>") || x.contains("<meta"))
    .map(stripTypeVar)
}

/**
 * Joern gets tripped up when generic classes are inherited from with a
 * specialized type variable. We need to strip out the type variable from the
 * class name.
 *
 * For example:
 *
 * class Foo(typing.Generic(T)):
 *    pass
 *
 * class IntFoo(Foo[int]):
 *    pass
 */
def stripTypeVar(className: String): String = className.takeWhile(_ != '[')

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
  val classReduceReturns: Iterator[Return] = reduceReturns.filter(_.method.typeDecl.head.fullName == classFullName)

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

    /* We expect that the class name on the queue is the full name of the
     * typeDecl. If no typeDecls are found with the given full name, then
     * either:
     * - The class name on the queue is not the full name. In this case,
     *   we look for any typeDecls with a short name that matches the class
     *   name, and add their full names to the queue. This may result in
     *   unrelated cases getting analyzed and widening our policies.
     * - The class name is a full name, but Joern does not recognize a node by
     *   that name. It may have the same node by a different name, or an error
     *   in its front end parsing.
     * - The class name is one that we have mangled - for example, any type
     *   found inside of a collection is currently named __collection.name, and
     *   needs to be unmangled.
     */
    val targetTypeDecls = cpg.typeDecl.fullName(targetClass).toList
    if (targetTypeDecls.isEmpty) {
      println(s"- !! unable to find typeDecl for class ${targetClass} !!")

      if (targetClass.startsWith("__collection.")) {
        /* Unmangle collection name */
        val strippedName = stripCollectionPrefix(targetClass)
        queue.enqueue(strippedName)
      } else {
        /* Lookup any typeDecls that match the short class name and add them to
         * queue.
         */
        val fullNames = cpg.typeDecl(targetClass).fullName.l
        println(s"-- found typeDecls with names: ${fullNames.mkString(",")}")
        fullNames.foreach(queue.enqueue)
      }

    } else {

      val reduceMethods = reduces(targetClass)
      if (reduceMethods.nonEmpty) {
        println(s"- reduce method identified")
        reduceMethods.foreach { r =>
          println(s"- adding callables: ${r.callable.fullName.mkString(",")}")
          allowedReduces ++= r.callable.fullName.toSet
          allowedGlobals ++= r.callable.fullName.toSet
        }

        // TODO: Analyze all types of arguments to reduceMethods

      } else {
        println(s"- no reduce method identified")
        allowedGlobals.add(targetClass)

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
        println(s"- parent classes: ${superClasses(targetClass).mkString(",")}")
        println(s"- parent class attribute types: ${parentAttributes.mkString(",")}")
        parentAttributes
          .filterNot(isPrimitiveType)
          .foreach(queue.enqueue)
      }
    }
  }

  (allowedGlobals.map(canonicalizeName(getPrefix(modelClass), _)),
   allowedReduces.map(canonicalizeName(getPrefix(modelClass), _)))
}

def getPrefix(input: String): String = {
  val index = input.indexOf('.')
  if (index == -1) input else input.substring(0, index)
}

def stripCollectionPrefix(input: String): String = {
  if (input.startsWith(CollectionPrefix)) input.substring(CollectionPrefix.length) else input
}

def canonicalizeName(baseModule: String, callableName: String): String = {

  // Split modelClass by PyModuleSuffix and take the first element
  val modelClassModule = baseModule

  // Some callables collected by Joern are suffixed with "<return_value>"
  // Remove this suffix
  def removeReturnValueSuffix(input: String): String = {
    val suffixPattern = "\\.<returnValue>$".r
    suffixPattern.replaceFirstIn(input, "")
  }

  def prependBaseModule(modulePrefix: String, input: String): String = {
    if (!input.contains(".")) s"$modulePrefix.$input" else input
  }

  // Split the callableName by PyModuleSuffix and stitch the components
  // together with '.'s
  val canonicalizedName = removeReturnValueSuffix(prependBaseModule(
    baseModule,
    stripCollectionPrefix(callableName)
    .replaceAllLiterally("/", ".")
    .replaceAllLiterally(PyModuleSuffix, ".")))

  return canonicalizedName
}

@main def main(inputPath: String, modelClass: String, outputPath: String = "") = {

  importCpg(inputPath)

  val (allowedGlobals, allowedReduces) = inferTypeFootprint(modelClass)

  val outputMap: Map[String, mutable.Set[String]] = Map(
      //"class_name" -> mutable.Set(modelClass),
      "globals" -> allowedGlobals,
      "reduces" -> allowedReduces)
  val jsonOutput: String = upickle.default.write(outputMap)
  val jsonString = ujson.read(jsonOutput)
  jsonString("class_name") = modelClass

  println()
  println(s"Allowed Globals: \n- ${allowedGlobals.mkString("\n- ")}")
  println(s"Allowed Reduces: \n- ${allowedReduces.mkString("\n- ")}")

  val outputFile = if (outputPath == "") {
    val outPath = os.Path(inputPath, base = os.pwd) / os.up
    outPath / "output.json"
  } else os.Path(outputPath, base = os.pwd)

  println()
  println(s"Writing output to file: ${outputFile}")
  os.write.over(outputFile, ujson.write(jsonString))
}
