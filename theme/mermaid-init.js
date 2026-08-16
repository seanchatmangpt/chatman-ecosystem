// Render Mermaid fences when the network can load the pinned ESM module.
// On import/render failure, the original fenced source is preserved.
document.addEventListener("DOMContentLoaded", async () => {
  const blocks = Array.from(document.querySelectorAll("pre code.language-mermaid"));
  if (blocks.length === 0) return;
  try {
    const module = await import("https://cdn.jsdelivr.net/npm/mermaid@11.16.0/dist/mermaid.esm.min.mjs");
    const mermaid = module.default;
    for (const code of blocks) {
      const pre = code.parentElement;
      if (!pre) continue;
      const div = document.createElement("div");
      div.className = "mermaid";
      div.textContent = code.textContent || "";
      pre.replaceWith(div);
    }
    mermaid.initialize({ startOnLoad: false, securityLevel: "strict" });
    await mermaid.run({ querySelector: ".mermaid" });
  } catch (error) {
    console.warn("Mermaid rendering unavailable; preserving source fences where possible.", error);
  }
});
