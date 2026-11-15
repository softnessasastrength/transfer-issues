// WP10 / EdgeHTML polyfills (integration shim — modern app untouched).
// Element.replaceChildren: absent from EdgeHTML (arrived Chromium Edge 86).
if (typeof Element !== 'undefined' && !Element.prototype.replaceChildren) {
  Element.prototype.replaceChildren = function () {
    while (this.firstChild) this.removeChild(this.firstChild);
    for (var i = 0; i < arguments.length; i++) {
      var n = arguments[i];
      this.appendChild(typeof n === 'string' ? document.createTextNode(n) : n);
    }
  };
}
// Object.fromEntries: ES2019, absent from EdgeHTML.
if (typeof Object.fromEntries !== 'function') {
  Object.fromEntries = function (entries) {
    var o = {};
    for (var i = 0; i < entries.length; i++) o[entries[i][0]] = entries[i][1];
    return o;
  };
}
// ChildNode.remove safety net.
if (typeof Element !== 'undefined' && !Element.prototype.remove) {
  Element.prototype.remove = function () { if (this.parentNode) this.parentNode.removeChild(this); };
}
