/*
 * Usage: ./joern --script ./analyze.sc --param inputPath=<path to python project cpg> --param modelClass=SequenceTagger
 */

import scala.collection.mutable.{Queue, Set}
import io.shiftleft.codepropertygraph.generated.nodes.{ TypeDecl, Method, FieldIdentifier, Call }

case class MemberType(
  name: String,
  types: IndexedSeq[String] = IndexedSeq.empty
)

/*
/* Return the set of all types of a given class's attributes */
def attributeTypes(classDecl: TypeDecl) : Iterator[MemberType] = {
  // TODO: Extend to also identify types stored in collections. Currently this isn't
  // captured by Joern, but when it is, this function will need more logic.
  classDecl.member.map(
    member => (
      MemberType(
        member.name,
        (member.typeFullName +: member.dynamicTypeHintFullName).filter(x => x != "ANY"))
    )
  )
}*/

// TODO
def getAttributeTypes(className: String): Iterator[String] = Iterator.empty

def printTypes(types: Iterator[MemberType]) = {
  for (mtype <- types) {
    println(mtype.name ++ ": " ++ mtype.types.mkString(","))
  }
}

def getSubClasses(parentClass: String): Iterator[String] = {
  cpg.typeDecl.filter(_.inheritsFromTypeFullName.contains(parentClass)).name // parentClass example: "model.py:<module>.Optimizer"
}

def getSuperClasses(className: String): Iterator[String] = {
  cpg.typeDecl(className).inheritsFromTypeFullName
}

// TODO: Neo has some code for this already
def getAllowedReduces(className: String): Iterator[String] = Iterator.empty

def isPrimitiveType(className: String) : Boolean = false

class UniqueQueue {

  val queue: Queue[String] = Queue.empty[String]
  val seen: Set[String] = Set.empty[String]

  def enqueue(className: String): Unit = {
    if (seen(className)) {
      queue.enqueue(className)
      seen.add(className)
    }
  }

  def dequeue: String = queue.dequeue

  def isEmpty: Boolean = queue.isEmpty

}

@main def main(inputPath: String, modelClass: String) = {

  importCpg(inputPath)

  /*
      analysisQueue := { modelClass }
      requiredClasses := EmptySet
      requiredReductions := EmptySet

      while analysisQueue notEmpty:

        currentClass := analysisQueue.dequeue()

        push parent / sub classes onto analysisQueue

        requiredCallable.push(currentClass)

        analysisQueue.enqueue( currentClass.attributeTypes )
        requiredReduction.push( currentClass.reduceFunctions )

      return requiredClasses, requiredReductions
  */

  /*
  var types = attributeTypes(cpg.typeDecl(modelClass).filter(_.isExternal==false).headOption.get)
  for (memberType <- types) {
    println(memberType.name ++ " -> " ++ memberType.types.mkString(","))
  }*/

  val allowedGlobals: Set[String] = Set()
  val allowedReduces: Set[String] = Set()

  val queue = UniqueQueue()
  queue.enqueue(modelClass)

  while (!queue.isEmpty) {

    val targetClass = queue.dequeue
    println(s"analyzing: ${targetClass}")

    getSuperClasses(targetClass)
      .foreach { c =>
        queue.enqueue(c)
      }

    getSubClasses(targetClass)
      .foreach { c =>
        queue.enqueue(c)
      }

    getAttributeTypes(targetClass)
      .filterNot(isPrimitiveType(_))
      .foreach { t =>
        queue.enqueue(t)
      }

    allowedGlobals.add(targetClass)
    getAllowedReduces(targetClass)
      .foreach { r =>
        allowedReduces.add(r)
      }
  }

  println(s"Allowed Globals: ${allowedGlobals.mkString("\n- ")}")
  println(s"Allowed Reduces: ${allowedReduces.mkString("\n- ")}")
}
