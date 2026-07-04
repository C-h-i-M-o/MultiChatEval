import DOMPurify from "dompurify";
import MarkdownIt from "markdown-it";
import markdownItKatex from "markdown-it-katex";

import { parseThinkContent } from "../features/evaluation/content";

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
}).use(markdownItKatex, {
  throwOnError: false,
  errorColor: "#bc442b"
});

const defaultLinkOpen =
  markdown.renderer.rules.link_open ||
  ((tokens, index, options, _environment, self) => self.renderToken(tokens, index, options));

markdown.renderer.rules.link_open = (tokens, index, options, env, self) => {
  const token = tokens[index];
  const targetIndex = token.attrIndex("target");
  const relIndex = token.attrIndex("rel");

  if (targetIndex < 0) {
    token.attrPush(["target", "_blank"]);
  } else if (token.attrs) {
    token.attrs[targetIndex][1] = "_blank";
  }

  if (relIndex < 0) {
    token.attrPush(["rel", "noopener noreferrer"]);
  } else if (token.attrs) {
    token.attrs[relIndex][1] = "noopener noreferrer";
  }

  return defaultLinkOpen(tokens, index, options, env, self);
};

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  const parsedContent = parseThinkContent(content);
  const answerHtml = renderMarkdownHtml(parsedContent.answer || "暂无回答内容");
  const thoughtHtml = parsedContent.thought ? renderMarkdownHtml(parsedContent.thought) : "";

  return (
    <div className="answer-text">
      {thoughtHtml ? (
        <details className="think-panel" open>
          <summary>思考过程</summary>
          <div className="markdown-body think-content" dangerouslySetInnerHTML={{ __html: thoughtHtml }} />
        </details>
      ) : null}
      <div className="markdown-body" dangerouslySetInnerHTML={{ __html: answerHtml }} />
    </div>
  );
}

export function renderMarkdownHtml(source: string): string {
  return sanitizeHtml(markdown.render(source));
}

function sanitizeHtml(html: string): string {
  const purifier = DOMPurify as unknown as {
    sanitize?: (dirty: string, config: { ADD_ATTR: string[]; ADD_TAGS: string[] }) => string;
  };
  if (!purifier.sanitize) {
    return html;
  }
  return purifier.sanitize(html, {
    ADD_ATTR: ["target", "style", "aria-hidden", "encoding"],
    ADD_TAGS: [
      "math",
      "semantics",
      "mrow",
      "mi",
      "mn",
      "mo",
      "msup",
      "msub",
      "msubsup",
      "mfrac",
      "msqrt",
      "mroot",
      "mtable",
      "mtr",
      "mtd",
      "mtext",
      "mstyle",
      "annotation"
    ]
  });
}
