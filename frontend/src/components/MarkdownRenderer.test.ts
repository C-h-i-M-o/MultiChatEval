import { describe, expect, test } from "vitest";

import { renderMarkdownHtml } from "./MarkdownRenderer";

describe("MarkdownRenderer", () => {
  test("支持单美元符号包裹的行内数学公式", () => {
    const html = renderMarkdownHtml("公式 $a^2+b^2=c^2$ 可以直接展示");

    expect(html).toContain("katex");
    expect(html).toContain("a^2+b^2=c^2");
  });

  test("支持双美元符号包裹的块级数学公式", () => {
    const html = renderMarkdownHtml("$$\nE=mc^2\n$$");

    expect(html).toContain("katex-display");
    expect(html).toContain("E=mc^2");
  });
});
