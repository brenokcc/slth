function StyleSheet(s) {
    let rule = "", rules = [], sheet = window.document.styleSheets[0]  // Get styleSheet
    s.split("}").forEach(s => {
      let r = (s + "}").replace(/\r?\n|\r/g, "");  // create full rule again
      rule = (rule === "") ? r : rule + r
      if (rule.split('{').length === rule.split('}').length) { // equal number of brackets?
        sheet.insertRule(rule, sheet.cssRules.length)
        rule = ""
      }
    })
  }

  export {StyleSheet};
  export default StyleSheet;