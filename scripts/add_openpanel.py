#!/usr/bin/env python3
"""Inject the OpenPanel tracking snippet into Base.astro (gated on PUBLIC_OPENPANEL_CLIENT_ID)."""
p = "/tmp/rv-web/src/layouts/Base.astro"
s = open(p).read()
if "openpanel" in s:
    print("already present")
    raise SystemExit
snippet = """  <script is:inline define:vars={{ openpanelClientId: import.meta.env.PUBLIC_OPENPANEL_CLIENT_ID }}>
    if (openpanelClientId) {
      window.op = window.op || function(){var n=[];return new Proxy(function(){arguments.length&&n.push([].slice.call(arguments))},{get:function(t,r){return"q"===r?n:function(){n.push([r].concat([].slice.call(arguments)))}},has:function(t,r){return"q"===r}}) }();
      window.op('init', {
        clientId: openpanelClientId,
        trackScreenViews: true,
        trackOutgoingLinks: true,
        trackAttributes: true,
      });
      var sc = document.createElement('script');
      sc.src = 'https://openpanel.dev/op1.js';
      sc.defer = true; sc.async = true;
      document.head.appendChild(sc);
    }
  </script>
</head>"""
s = s.replace("</head>", snippet, 1)
open(p, "w").write(s)
print("openpanel snippet in Base.astro")
