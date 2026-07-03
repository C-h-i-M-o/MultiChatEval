import DOMPurify from "dompurify";
import MarkdownIt from "markdown-it";

import { parseThinkContent } from "../features/evaluation/content";

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
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
  const answerHtml = sanitizeMarkdown(parsedContent.answer || "暂无回答内容");
  const thoughtHtml = parsedContent.thought ? sanitizeMarkdown(parsedContent.thought) : "";

  return (
    <div className="answer-text">
      {thoughtHtml ? (
        <details className="think-panel">
          <summary>思考过程</summary>
          <div className="markdown-body think-content" dangerouslySetInnerHTML={{ __html: thoughtHtml }} />
        </details>
      ) : null}
      <div className="markdown-body" dangerouslySetInnerHTML={{ __html: answerHtml }} />
    </div>
  );
}

function sanitizeMarkdown(source: string): string {
  return DOMPurify.sanitize(markdown.render(source), {
    ADD_ATTR: ["target"]
  });
}
