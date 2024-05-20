/*
 * Usage: ./joern --script ./analyze.sc --param inputPath=<path to python project source> --param modelClass=SequenceTagger
 */

import io.shiftleft.codepropertygraph.generated.nodes.TypeDecl

case class MemberType(
  name: String,
  types: IndexedSeq[String] = IndexedSeq.empty
)

/* Return the set of all types of a given class's attributes */
def attributeTypes(classDecl: TypeDecl) : Iterator[MemberType] = {
  classDecl.member.map(
    member => (
      MemberType(
        member.name,
        (member.typeFullName +: member.dynamicTypeHintFullName).filter(x => x != "ANY"))
    )
  )
}

def printTypes(types: Iterator[MemberType]) = {
  for (mtype <- types) {
    println(mtype.name ++ ": " ++ mtype.types.mkString(","))
  }
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


  var types = attributeTypes(cpg.typeDecl(modelClass).filter(_.isExternal==false).headOption.get)
  for (memberType <- types) {
    println(memberType.name ++ " -> " ++ memberType.types.mkString(","))
  }
}
