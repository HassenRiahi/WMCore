function(doc) {
  if (doc.type == "jobsummary") {
    var listErrors = [];
    for (var step in doc.errors) {
        for (var out in doc.errors[step]) {
            if ('type' in doc.errors[step][out]) {
                listErrors.push(doc.errors[step][out]["type"]);
            }
        }
    }
    listErrors.sort();
    emit([doc.workflow, doc.state, doc.exitcode, doc.site, listErrors], {"id": doc.id});
  }
}
