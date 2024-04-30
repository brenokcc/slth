(function webpackUniversalModuleDefinition(root, factory) {
  window.reactTriggerChange = factory();
})(this, function () {
  return (function (modules) {
    var installedModules = {};
    function __webpack_require__(moduleId) {
      if (installedModules[moduleId]) return installedModules[moduleId].exports;
      var module = (installedModules[moduleId] = {
        i: moduleId,
        l: false,
        exports: {},
      });
      modules[moduleId].call(
        module.exports,
        module,
        module.exports,
        __webpack_require__
      );
      module.l = true;
      return module.exports;
    }
    __webpack_require__.m = modules;
    __webpack_require__.c = installedModules;
    __webpack_require__.i = function (value) {
      return value;
    };
    __webpack_require__.d = function (exports, name, getter) {
      if (!__webpack_require__.o(exports, name)) {
        Object.defineProperty(exports, name, {
          configurable: false,
          enumerable: true,
          get: getter,
        });
      }
    };
    __webpack_require__.n = function (module) {
      var getter =
        module && module.__esModule
          ? function getDefault() {
              return module["default"];
            }
          : function getModuleExports() {
              return module;
            };
      __webpack_require__.d(getter, "a", getter);
      return getter;
    };
    __webpack_require__.o = function (object, property) {
      return Object.prototype.hasOwnProperty.call(object, property);
    };
    __webpack_require__.p = "";
    return __webpack_require__((__webpack_require__.s = 0));
  })([
    function (module, exports, __webpack_require__) {
      "use strict";
      module.exports = function reactTriggerChange(node) {
        var supportedInputTypes = {
          color: true,
          date: true,
          datetime: true,
          "datetime-local": true,
          email: true,
          month: true,
          number: true,
          password: true,
          range: true,
          search: true,
          tel: true,
          text: true,
          time: true,
          url: true,
          week: true,
        };
        var nodeName = node.nodeName.toLowerCase();
        var type = node.type;
        var event;
        var descriptor;
        var initialValue;
        var initialChecked;
        var initialCheckedRadio;

        function deletePropertySafe(elem, prop) {
          var desc = Object.getOwnPropertyDescriptor(elem, prop);
          if (desc && desc.configurable) {
            delete elem[prop];
          }
        }

        function changeRangeValue(range) {
          var initMin = range.min;
          var initMax = range.max;
          var initStep = range.step;
          var initVal = Number(range.value);

          range.min = initVal;
          range.max = initVal + 1;
          range.step = 1;
          range.value = initVal + 1;
          deletePropertySafe(range, "value");
          range.min = initMin;
          range.max = initMax;
          range.step = initStep;
          range.value = initVal;
        }

        function getCheckedRadio(radio) {
          var name = radio.name;
          var radios;
          var i;
          if (name) {
            radios = document.querySelectorAll(
              'input[type="radio"][name="' + name + '"]'
            );
            for (i = 0; i < radios.length; i += 1) {
              if (radios[i].checked) {
                return radios[i] !== radio ? radios[i] : null;
              }
            }
          }
          return null;
        }

        function preventChecking(e) {
          e.preventDefault();
          if (!initialChecked) {
            e.target.checked = false;
          }
          if (initialCheckedRadio) {
            initialCheckedRadio.checked = true;
          }
        }

        if (
          nodeName === "select" ||
          (nodeName === "input" && type === "file")
        ) {
          event = document.createEvent("HTMLEvents");
          event.initEvent("change", true, false);
          node.dispatchEvent(event);
        } else if (
          (nodeName === "input" && supportedInputTypes[type]) ||
          nodeName === "textarea"
        ) {
          descriptor = Object.getOwnPropertyDescriptor(node, "value");
          event = document.createEvent("UIEvents");
          event.initEvent("focus", false, false);
          node.dispatchEvent(event);
          if (type === "range") {
            changeRangeValue(node);
          } else {
            initialValue = node.value;
            node.value = initialValue + "#";
            deletePropertySafe(node, "value");
            node.value = initialValue;
          }
          event = document.createEvent("HTMLEvents");
          event.initEvent("propertychange", false, false);
          event.propertyName = "value";
          node.dispatchEvent(event);
          event = document.createEvent("HTMLEvents");
          event.initEvent("input", true, false);
          node.dispatchEvent(event);
          if (descriptor) {
            Object.defineProperty(node, "value", descriptor);
          }
        } else if (nodeName === "input" && type === "checkbox") {
          node.checked = !node.checked;
          event = document.createEvent("MouseEvents");
          event.initEvent("click", true, true);
          node.dispatchEvent(event);
        } else if (nodeName === "input" && type === "radio") {
          initialChecked = node.checked;
          initialCheckedRadio = getCheckedRadio(node);
          descriptor = Object.getOwnPropertyDescriptor(node, "checked");
          node.checked = !initialChecked;
          deletePropertySafe(node, "checked");
          node.checked = initialChecked;
          node.addEventListener("click", preventChecking, true);
          event = document.createEvent("MouseEvents");
          event.initEvent("click", true, true);
          node.dispatchEvent(event);
          node.removeEventListener("click", preventChecking, true);
          if (descriptor) {
            Object.defineProperty(node, "checked", descriptor);
          }
        }
      };
    },
  ]);
});
