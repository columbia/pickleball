/*
 * Usage: ./joern --script ./analyze.scala --param inputPath=<path to python project cpg> --param modelClass=SequenceTagger
 */

import scala.collection.mutable
import io.shiftleft.codepropertygraph.generated.nodes.{ TypeDecl, Method, FieldIdentifier, Call }

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
  cpg.typeDecl
    .fullName(className)
    .inheritsFromTypeFullName
    .filterNot(_ == "object")
    .filterNot(x => x.startsWith("<body>") || x.startsWith("<fakeNew>") || x.startsWith("<meta"))
}

// TODO: Neo has some code for this already
def reduces(className: String): Iterator[String] = Iterator.empty

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

@main def main(inputPath: String, modelClass: String) = {

  importCpg(inputPath)

  val allowedGlobals: mutable.Set[String] = mutable.Set()
  val allowedReduces: mutable.Set[String] = mutable.Set()

  val queue: UniqueQueue[String] = UniqueQueue()
  queue.enqueue(modelClass)

  while (!queue.isEmpty) {

    val targetClass = queue.dequeue
    println(s"analyzing: ${targetClass}")

    // Should not add super classes to allowed sets, but should ensure that all
    // attributes are analyzed, since they can be attributes of the current
    // class.
    // FIXME
    superClasses(targetClass)
      .foreach { c =>
        queue.enqueue(c)
      }

    // Must add all subclasses to the allowed sets.
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
