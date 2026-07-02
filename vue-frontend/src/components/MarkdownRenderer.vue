<template>
  <div class="answer-text">
    <details v-if="renderedThoughtHtml" class="think-panel">
      <summary>思考过程</summary>
      <div class="markdown-body think-content" v-html="renderedThoughtHtml"></div>
    </details>
    <div class="markdown-body" v-html="renderedAnswerHtml"></div>
  </div>
</template>

<script setup>
import DOMPurify from "dompurify";
import MarkdownIt from "markdown-it";
import { computed } from "vue";

const props = defineProps({
  content: {
    type: String,
    default: ""
  }
});

const markdown = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true
});

const defaultLinkOpen =
  markdown.renderer.rules.link_open ||
  ((tokens, index, options, env, self) => self.renderToken(tokens, index, options));

markdown.renderer.rules.link_open = (tokens, index, options, env, self) => {
  const token = tokens[index];
  const targetIndex = token.attrIndex("target");
  const relIndex = token.attrIndex("rel");

  if (targetIndex < 0) {
    token.attrPush(["target", "_blank"]);
  } else {
    token.attrs[targetIndex][1] = "_blank";
  }

  if (relIndex < 0) {
    token.attrPush(["rel", "noopener noreferrer"]);
  } else {
    token.attrs[relIndex][1] = "noopener noreferrer";
  }

  return defaultLinkOpen(tokens, index, options, env, self);
};

function sanitizeMarkdown(source) {
  return DOMPurify.sanitize(markdown.render(source), {
    ADD_ATTR: ["target"]
  });
}

function parseThinkContent(content) {
  const source = content || "";
  const thoughts = [];
  let answer = source;

  answer = answer.replace(/<think>([\s\S]*?)<\/think>/gi, (_, thought) => {
    thoughts.push(thought.trim());
    return "";
  });

  const unmatchedStart = answer.search(/<think>/i);
  if (unmatchedStart >= 0) {
    const thought = answer.slice(unmatchedStart).replace(/<think>/i, "").trim();
    thoughts.push(thought);
    answer = answer.slice(0, unmatchedStart);
  }

  return {
    answer: answer.trim(),
    thought: thoughts.filter(Boolean).join("\n\n---\n\n")
  };
}

const parsedContent = computed(() => parseThinkContent(props.content));

const renderedThoughtHtml = computed(() => {
  if (!parsedContent.value.thought) {
    return "";
  }
  return sanitizeMarkdown(parsedContent.value.thought);
});

const renderedAnswerHtml = computed(() => {
  const source = parsedContent.value.answer || "暂无回答内容";
  return sanitizeMarkdown(source);
});
</script>
