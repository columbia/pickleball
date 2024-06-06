/*
 * Usage: ./joern --script ./analyze.scala --param inputPath=<path to python project cpg> --param modelClass=SequenceTagger
 */

import scala.collection.mutable.{Queue, Set}
import io.shiftleft.codepropertygraph.generated.nodes.{ TypeDecl, Method, FieldIdentifier, Call }

// TODO: Need to turn module / name format into something I can use to properly
// query the CPG

def attributeTypes(className: String): Iterator[String] = {
  /* TODO: Handle types stored in collections */
  cpg.typeDecl(className).member.flatMap {
    member =>
      (member.typeFullName +: member.dynamicTypeHintFullName)
        .filterNot(_ == "ANY")
        .filterNot(isPrimitiveType(_))
        .distinct
  }
}

def subClasses(parentClass: String): Iterator[String] = {
  cpg.typeDecl
    .filter(_.inheritsFromTypeFullName.contains(parentClass))
    .name
    .filterNot(_ == "object")
}

def superClasses(className: String): Iterator[String] = {
  cpg.typeDecl(className).inheritsFromTypeFullName.filterNot(_ == "object")
}

// TODO: Neo has some code for this already
def reduces(className: String): Iterator[String] = Iterator.empty

def isPrimitiveType(className: String) : Boolean = className.startsWith("__builtin.")

class UniqueQueue[T] extends Queue[T] {

  val seen: Set[T] = Set.empty[T]

  override def enqueue(obj: T): UniqueQueue.this.type = {
    if (!seen(obj)) {
      seen.add(obj)
      super.enqueue(obj)
    } else { this }
  }

}

@main def main(inputPath: String, modelClass: String) = {

  importCpg(inputPath)

  val allowedGlobals: Set[String] = Set()
  val allowedReduces: Set[String] = Set()

  val queue: UniqueQueue[String] = UniqueQueue()
  queue.enqueue(modelClass)

  while (!queue.isEmpty) {

    val targetClass = queue.dequeue
    println(s"analyzing: ${targetClass}")

    superClasses(targetClass)
      .foreach { c =>
        queue.enqueue(c)
      }

    subClasses(targetClass)
      .foreach { c =>
        queue.enqueue(c)
      }

    attributeTypes(targetClass)
      .filterNot(isPrimitiveType(_))
      .foreach { t =>
        queue.enqueue(t)
      }

    allowedGlobals.add(targetClass)
    reduces(targetClass)
      .foreach { r =>
        allowedReduces.add(r)
      }
  }

  println(s"Allowed Globals: ${allowedGlobals.mkString("\n- ")}")
  println(s"Allowed Reduces: ${allowedReduces.mkString("\n- ")}")
}
