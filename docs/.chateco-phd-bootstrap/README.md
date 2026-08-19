# Chateco PhD publication bootstrap

This transient directory carries only the content-addressed transport for the full Markdown manuscript.
The `Chateco PhD Book` workflow verifies archive SHA-256 `e90331785c29d0535ffad6f9e60167b671b148e609b0781fcb25f1fa36b144b4`, refuses out-of-scope archive paths or links, expands `docs/chateco-phd/**`, runs the manuscript verifier and mdBook 0.5.4 build, then removes this directory before committing the full source tree.
