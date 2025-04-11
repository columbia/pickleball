/*
 * Usage: ./joern --script ./analyze.sc --param inputPath=<path to python project cpg> --param modelClass=SequenceTagger --param outputPath=<path to output> --param cache=<path to cache directory>
 */

import scala.collection.mutable
import io.shiftleft.codepropertygraph.generated.nodes.{
  Return, TypeDecl, Method, Identifier, FieldIdentifier, Literal, Call => CallNode }

import scala.io.Source
import java.io.File

val PyModuleSuffix = ".py:<module>."
val ModuleSuffix = ":<module>."
val CollectionPrefix ="__collection."
val JoernBuiltinPrefix = "__builtin."

/**
 * Some PyTorch imports use aliased module names. PickleBall will identify
 * the aliased name, because that is how they are referenced in the analyzed
 * source code, but pickle programs use the fully qualified names.
 *
 * We provide a map of some alias names to FQNs for common imports.
 */
val commonImportMappings: Map[String, String] = Map(
  "torch.nn.Conv2d" -> "torch.nn.modules.conv.Conv2d",
  "torch.nn.BatchNorm2d" -> "torch.nn.modules.batchnorm.BatchNorm2d",
  "torch.nn.SiLU" -> "torch.nn.modules.activation.SiLU",
  "torch.nn.ModuleList" -> "torch.nn.modules.container.ModuleList",
  "torch.nn.Sequential" -> "torch.nn.modules.container.Sequential",
  "torch.nn.MaxPool2d" -> "torch.nn.modules.pooling.MaxPool2d",
  "torch.nn.Identity" -> "torch.nn.modules.linear.Identity",
  "torch.nn.Upsample" -> "torch.nn.modules.upsampling.Upsample"
)

/**
 * Joern struggles to distinguish between class constructors and function call
 * return types - all are marked in the AST similarly (and Joern does not have
 * type decl access for standard library functions.)
 *
 * We provide some known container constructors that Joern misses.
 */
val knownConstructors: Set[String] = Set(
  "collections.py:<module>.defaultdict.<returnValue>",
)

type ClassPolicy = Map[String, Set[String]]
type PolicyMap = Map[String, ClassPolicy]

def attributeTypes(className: String): Iterator[String] = {
  /* TODO: Handle types stored in collections */
  cpg.typeDecl.fullName(className).member.flatMap {
    member =>
      (member.typeFullName +: member.dynamicTypeHintFullName)
        .filterNot(_.matches("object|ANY"))
        //.filterNot(isPrimitiveType(_))
        /*  Constructors assigned to attributes may result in types of
         *  Class.__init__ or Class.__init__.<returnValue>. When these are
         *  seen, we can strip the suffix and just add the class name to the
         *  analysis Queue.
         * */
        .map { memberType =>
          memberType match {
            /* Permit and simplify members that end with __init__ and __init.<returnValue>
             * as they are class constructors. (Also <metaClassAdapter> wrapper.)
             * Do not permit members that just end with <returnValue> because these are
             * methods, not types. Eventually, better type recovery would turn these into
             * the recovered class types.
             */
            case s if s.endsWith(".__init__.<returnValue>") => s.stripSuffix(".__init__.<returnValue>")
            case s if s.endsWith(".__init__") => s.stripSuffix(".__init__")
            //case s if s.endsWith(".<returnValue>") => s.stripSuffix(".<returnValue>")
            case s if knownConstructors.contains(s) => s.stripSuffix("<returnValue>")
            case s if s.endsWith("<metaClassAdapter>") => s.stripSuffix("<metaClassAdapter>")
            case _ => memberType
          }
        }
        .map { memberType => removeMemberWrapper(memberType) }
        .filterNot(_.endsWith(".<returnValue>"))
        .distinct
  }
}

def subClasses(inputParentClass: String): Iterator[String] = {
  /* Identify all type declarations that inherit from the parentClass */

  val parentClass = stripPrefix(JoernBuiltinPrefix, inputParentClass)

  cpg.typeDecl
    .filter(_.inheritsFromTypeFullName.contains(parentClass))
    .fullName
    .filterNot(_.matches("object|ANY"))
    .filterNot(x => x.contains("<body>") || x.contains("<fakeNew>") || x.contains("<meta"))
}

def superClasses(inputClassName: String): Seq[String] = {
 /**
 * Sometimes type information is in both the inheritsFromTypeFullName and the
 * baseType fields (or one, and not the other). We try searching for both.
 */

val className = stripPrefix(JoernBuiltinPrefix, inputClassName)

val parents = (cpg.typeDecl
    .fullName(className)
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
    .map(stripTypeVar)).distinct.toSeq
  parents match {
    case Seq() => parents
    case ps => parents ++ parents.flatMap(superClasses)
  }
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
  callable:   Option[String],
  retloc:     String
)

// val reduceReturns = cpg.ret.filter(_.method.name.matches("_reduce_ex__|__reduce__"))

def constructReduceCallables(callableName: String, classDecl: TypeDecl, retLoc: String): Set[ReduceCallable] = {
  /*cpg.method.filter(_.fullName == callableName).l match {
    case Nil => Set()
    case callables => callables.map(callable =>
      println(s"- constructing callable for ${classDecl.name}:${callable.name}")
      ReduceCallable(Some(classDecl), Some(callable), retLoc)).toSet
  }*/
  println(s"- constructing callable for ${classDecl.name}:${callableName}")
  Set(ReduceCallable(Some(classDecl), Some(callableName), retLoc))
}

/*
 * Given a return statement in a __reduce__ or __reduce_ex__ method, determine
 * the returned callable object. Also takes the typeDecl of the class that
 * implements the __reduce__ method.
 *
 * TODO: The types also contained in the tuples need to be checked as well.
 */
def callablesFromReduceReturn(ret: Return, pclass: TypeDecl, analyzedClass: String): Set[ReduceCallable] = {
  val retLoc = s"${ret.method.filename}:${ret.lineNumber.getOrElse(-1)}"

  /*
   * The return value of a reduce call can either be: a string literal, a tuple,
   * or an expression that we need to recursively descend into.
   */
  ret.argumentOut.l match {

    case Nil =>
      println(s"Unknown reduce return value for ${ret} @ ${retLoc}")
      Set(ReduceCallable(None, None, retLoc))

    case retVal :: _ =>
      retVal match {
        case literal: Literal if literal.typeFullName == "__builtin.str" =>

          /* The return statement is a string literal */
          println(s"- string literal: ${literal.code.replace("\"", "")}")

          constructReduceCallables(literal.code.replace("\"", ""), pclass, retLoc)

        case call: CallNode if call.methodFullName == "<operator>.tupleLiteral" =>

          /* The return statement is a tuple of return values */
          println(s"- tuple: ${call.name}")

          /* Check the elements of the tuple - the first element is the
           * returned callable (most important) while the others are treated
           * for arguments.
           */
          call.argument.l match {
            case Nil => Set()

            case (returnCallableIdentifier: Identifier) :: _ =>
              /* Callable return value is a method name defined in the same
               * file. Add the correct module full name prefix
               */
              val callableName = s"${call.method.filename}${ModuleSuffix}${returnCallableIdentifier.name}"
              println(s"- callable name: ${callableName}")
              constructReduceCallables(callableName, pclass, retLoc)

            case (returnCallableFieldAccess: CallNode) :: _ if returnCallableFieldAccess.name == "<operator>.fieldAccess" =>
              /* Callable return value is a field access node (can occur when returned
               * callable is a method or attribute, like: `self.__class__`
               */

              /* TODO: Refactor functionally */
              var fieldAccess = returnCallableFieldAccess
              var fieldAccessBase = fieldAccess.argument.l(0)
              var fieldAccessIdentifier: FieldIdentifier = fieldAccess.argument.l(1).asInstanceOf[FieldIdentifier]
              var fullName = fieldAccessIdentifier.canonicalName

              while (fieldAccessBase.isCall && fieldAccessBase.asInstanceOf[CallNode].name == "<operator>.fieldAccess") {
                /* I believe this occurs when the return value is a nested
                 * field access, like: self.model.__class__
                 *
                 * Must walk the field accesses until the identifier is found.
                 *
                 * TODO: Test this code - I don't think it works as intended.
                 */
                fieldAccess = fieldAccessBase.asInstanceOf[CallNode]
                fieldAccessBase = fieldAccess.argument.l(0)
                fieldAccessIdentifier = fieldAccess.argument.l(1).asInstanceOf[FieldIdentifier]
                fullName = fieldAccessIdentifier.canonicalName + PyModuleSuffix + fullName
              }
              if (fieldAccessBase.isIdentifier && fieldAccessBase.asInstanceOf[Identifier].name == "self") {
                fullName = analyzedClass + "." + fullName
                /* println(s"Unknown identifier for reduce return value ${fieldAccessBase.asInstanceOf[Identifier].name}") */
              }
              println(s"fullName: ${fullName}")
              constructReduceCallables(fullName, pclass, retLoc)

            case (arg0: CallNode) :: _ => /* Error */
              /* Callable return value is some other call node - should not occur */
              println(s"Unknown call for reduce return value ${arg0.name}")
              Set()
          }

        case call: CallNode =>

          /* The return statement contains some other call expression
           * TODO: Provide example of why this could happen
           *
           * Handle expression by recursively descending to get return values
           */
          println(s"- call: ${call.name}")
          val returns = cpg.ret.filter(_.method.name == call.name)
          returns.flatMap {newRet => callablesFromReduceReturn(newRet, pclass, analyzedClass) }.toSet

        case _ =>
          println(s"Unknown reduce return value @ ${retLoc}")
          Set(ReduceCallable(None, None, retLoc))
      }
  }
}

/* Given a class name, return all the callables that the class __reduce__|__reduce_ex__
 * method returns, if it exists.
 */
def reduces(classFullName: String): Iterator[ReduceCallable] = {

  val reduceReturns = cpg.ret.filter(_.method.name.matches("__reduce_ex__|__reduce__"))
  val classHierarchy = classFullName +: superClasses(classFullName)
  val classReduceReturns: Iterator[Return] = reduceReturns.filter(retStmt => classHierarchy.contains(retStmt.method.typeDecl.head.fullName))
  //val classReduceReturns: Iterator[Return] = reduceReturns.filter(_.method.typeDecl.head.fullName == classFullName)

  classReduceReturns.flatMap { ret =>
    println(s"Analyzing return statement ${ret} @ ${ret.method.filename}:${ret.lineNumber.getOrElse(-1)}")
    val pclass = ret.method.typeDecl.head   // may nead headOption - occurs if the __reduce__ method is not in a class, which shouldn't be the case
    callablesFromReduceReturn(ret, pclass, classFullName)
  }
}

def isPrimitiveType(className: String) : Boolean = className.startsWith(JoernBuiltinPrefix)

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

// TODO: Print output to log
def inferTypeFootprint(modelClass: String, cachedPolicies: PolicyMap): (mutable.Set[String], mutable.Set[String]) = {

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
    val tempClass: String = cachedPolicies.keys.find(key => targetClass.startsWith(key)).getOrElse("")

    if (tempClass.nonEmpty) {
      /* Candidate class is in the policy cache */

      println(s"- found target class \"${targetClass}\" in type cache")
      val classPolicy: Option[ClassPolicy] = cachedPolicies.get(tempClass)

      classPolicy match {
        case Some(policy) =>
          val globals: Set[String] = policy.getOrElse("globals", Set.empty)
          val reduces: Set[String] = policy.getOrElse("reduces", Set.empty)
          allowedGlobals ++= (globals + targetClass)
          allowedReduces ++= reduces
        case _ =>
      }

      /** still need to check if the cached class is inherited from other classes */
      println(s"- sub classes: ${subClasses(targetClass).toList.mkString(",")}")
      subClasses(targetClass).foreach(queue.enqueue)

    } else if (targetTypeDecls.isEmpty && !targetClass.startsWith(JoernBuiltinPrefix)) {
      /* Candidate class is neither in the CPG nor in the policy cache because:
       * 1. Candidate class might be a mangled name
       *      => unmangle name and add new name to queue
       * 2. Candidate class might be a short name
       *      => look up full name of objects and add to queue
       *         (might result in imprecision)
       * 3. Candidate class is in an external library
       *      => TODO: fetch library for analysis
       * 4. Candidate class is a builtin type and therefore has no typedecl - (proceed to analysis below)
       */

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

        if (fullNames.isEmpty) {
          println(s"-- found no alternatives, allowing ${targetClass}")
          allowedGlobals += targetClass
        } else {
          println(s"-- found typeDecls with names: ${fullNames.mkString(",")}")
          fullNames.foreach(queue.enqueue)
        }
      }

    } else {
      /* Candidate class is in CPG and must be analyzed */

      /* Find first reduce method in class hierarchy and return a reference
          to it */

      val reduceMethods = reduces(targetClass)
      if (reduceMethods.nonEmpty) {
        /* Candidate class implements a __reduce__ method */
        println(s"- reduce method identified")

        reduceMethods.foreach { r =>
          println(s"- adding callables: ${r.callable}")
          allowedReduces ++= r.callable.toSet
          allowedGlobals ++= r.callable.toSet
        }

        // TODO: Analyze all types of arguments to reduceMethods

      } else {
        /* Candidate class does not implement a __reduce__ method */
        println(s"- no reduce method identified")
        allowedGlobals.add(targetClass)

        /** Analyze all subclasses of targetClass */
        println(s"- sub classes: ${subClasses(targetClass).toList.mkString(",")}")
        subClasses(targetClass).foreach(queue.enqueue)

        /** Approximate all types that can be written to attributes of the targetClass
         * analyzing all class attribute types. */

        // TODO: What if a cached ancestor class implements a __reduce__ method?

        val classAttributeTypes: List[String] = attributeTypes(targetClass).toList
        println(s"- attribute types: ${classAttributeTypes.toList.mkString(",")}")
        classAttributeTypes.foreach(queue.enqueue)

        /* Ensure that attribute types of parent classes are also collected */
        val ancestors: Seq[String] = superClasses(targetClass)
        println(s"- parent classes: ${ancestors.mkString(",")}")

        /* Partition the ancestors according to whether they are contained in
         * the cache, and handle cached ancestors separately
         */
        val (cachedAncestors, newAncestors) = ancestors.partition(ancestor => cachedPolicies.contains(ancestor))
        cachedAncestors.map { ancestor =>
          /* This is a repeat of how a cached ancestor is handled, from above.
           * This should be handled in one place
           * TODO: Refactor
           */
          println(s"- found parent class \"${ancestor}\" in type cache")
          val classPolicy: Option[ClassPolicy] = cachedPolicies.get(ancestor)

          classPolicy match {
            case Some(policy) =>
              val globals: Set[String] = policy.getOrElse("globals", Set.empty) - canonicalizeName(getPrefix(ancestor), ancestor) // We do not add the ancestor class
              val reduces: Set[String] = policy.getOrElse("reduces", Set.empty)

              println(s"-- adding cached globals: ${globals.mkString(",")}")
              println(s"-- adding cached reduces: ${reduces.mkString(",")}")
              allowedGlobals ++= globals
              allowedReduces ++= reduces
            case _ =>
          }

          /** still need to check if the cached class is inherited from other classes */
          println(s"- sub classes: ${subClasses(ancestor).toList.mkString(",")}")
          subClasses(ancestor).foreach(queue.enqueue)
        }

        val ancestorAttributes: List[String] = newAncestors.flatMap(attributeTypes).toList
        println(s"- inferred parent class attribute types: ${ancestorAttributes.mkString(",")}")
        ancestorAttributes
          .foreach(queue.enqueue)
      }
    }
  }

  /** If any callables are in the known mapped imports, insert the mappings
   * as well.
   */
  def enrichWithKnownAliases(input: mutable.Set[String]): mutable.Set[String] = {
    input ++ input.flatMap(commonImportMappings.get)
  }

  /** Python3 uses both __builtin__ and builtins - add any __builtin__ with a
   * builtins version
   */
  def handleBuiltins(s: mutable.Set[String]): mutable.Set[String] = {
    s ++ s.collect {
      case s if s.startsWith("__builtin__.") =>
        //s.replaceFirstLiterally("__builtin__.", "builtins.")
        s.replaceFirst(java.util.regex.Pattern.quote("__builtin__."), "builtins.")
    }
  }

  def postProcessCallables: mutable.Set[String] => mutable.Set[String] = {
    (s: mutable.Set[String]) => enrichWithKnownAliases(handleBuiltins(s))
  }

  (postProcessCallables(allowedGlobals.map(canonicalizeName(getPrefix(modelClass), _))),
   postProcessCallables(allowedReduces.map(canonicalizeName(getPrefix(modelClass), _))))
}

def getPrefix(input: String): String = {
  val index = input.indexOf('.')
  if (index == -1) input else input.substring(0, index)
}

def stripCollectionPrefix(input: String): String = stripPrefix(CollectionPrefix, input)

def removeMemberWrapper(input: String): String = {
  val memberPattern = """<member>\(([^)]+)\)""".r
  memberPattern.replaceAllIn(input, m => m.group(1))
}

def stripPrefix(prefix: String, input: String): String = {
  if (input.startsWith(prefix)) input.substring(prefix.length) else input
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

  /* Treat Python special purpose method: __class__
   * TODO: Determine if this is actually the best place to treat this
   */
  def removeClassSuffix(input: String): String = {
    val suffixPattern = "\\.__class__$".r
    suffixPattern.replaceFirstIn(input, "")
  }

  def prependBaseModule(modulePrefix: String, input: String): String = {
    if (!input.contains(".")) s"$modulePrefix.$input" else input
  }

  // Split the callableName by PyModuleSuffix and stitch the components
  // together with '.'s
  val canonicalizedName = removeClassSuffix(removeReturnValueSuffix(prependBaseModule(
    baseModule,
    stripCollectionPrefix(callableName)
    .replace("/", ".")
    .replace(PyModuleSuffix, "."))))
    /* If canonicalized name begins with __builtin, replace with __builtin__. */
    .replace(JoernBuiltinPrefix, "__builtin__.")

  return canonicalizedName
}

def readCache(cachePath: String): PolicyMap = {
  if (cachePath.isEmpty) return Map.empty

  val cacheDir = new File(cachePath)
  if (!cacheDir.exists || !cacheDir.isDirectory) return Map.empty

  // Read and parse a single JSON file
  def parseJsonFile(file: File): Option[PolicyMap] = {
    val source = Source.fromFile(file)
    val jsonStr = try source.mkString finally source.close()

    try {
      val jsonValue: ujson.Value = ujson.read(jsonStr)
      Some(
        jsonValue.obj.toMap.map { case (className, policies) =>
          val globals = policies("globals").arr.map(_.str).toSet
          val reduces = policies("reduces").arr.map(_.str).toSet
          className -> Map("globals" -> globals, "reduces" -> reduces)
        }
      )
    } catch {
      case _: Throwable =>
        println(s"Invalid cached policy found: ${file.getName()}")
        None // Return None for malformed JSON
    }
  }

  // Read all JSON files and merge their contents into a PolicyMap
  val allJsonMaps: Array[PolicyMap] = cacheDir.listFiles.filter(_.isFile).flatMap(parseJsonFile)
  allJsonMaps.foldLeft(Map[String, ClassPolicy]()) { (acc, policyMap) =>
    acc ++ policyMap
  }
}

@main def main(inputPath: String, modelClass: String, outputPath: String = "", cache: String = "") = {

  importCpg(inputPath)

  val cachedPolicies: PolicyMap = readCache(cache)
  println(s"${cachedPolicies.mkString(",")}")

  val (allowedGlobals, allowedReduces) = inferTypeFootprint(modelClass, cachedPolicies)

  val classPolicy: ClassPolicy = Map(
      "globals" -> allowedGlobals.toSet,
      "reduces" -> allowedReduces.toSet)
  val policy: PolicyMap = Map(modelClass -> classPolicy)
  val jsonPolicy: String = upickle.default.write(policy)
  val jsonString = ujson.read(jsonPolicy)

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
