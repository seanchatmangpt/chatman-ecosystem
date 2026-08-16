document.addEventListener("DOMContentLoaded", async () => {
  const blocks = Array.from(document.querySelectorAll("pre code.language-mermaid"));
  if (blocks.length === 0) return;

  for (const block of blocks) {
    const container = document.createElement("div");
    container.className = "mermaid";
    container.textContent = block.textContent;
    block.parentElement.replaceWith(container);
  }

  try {
    const module = await import(
      "https://cdn.jsdelivr.net/npm/mermaid@11.15.0/dist/mermaid.esm.min.mjs"
    );
    const mermaid = module.default;
    mermaid.initialize({
      startOnLoad: false,
      securityLevel: "strict",
      theme: "neutral"
    });
    await mermaid.run({ querySelector: ".mermaid" });
  } catch (error) {
    console.error("Mermaid rendering failed", error);
  }
});
