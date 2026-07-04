import { useLayoutEffect, useRef, useState } from "react";
import { Button, Modal, Space } from "antd";

import { animateModalIn } from "../animations/pageMotion";
import { isPendingResponse } from "../features/evaluation/evaluation";
import type { DisplayModelResponse, EvaluationScore, FeedbackToggleResult } from "../features/evaluation/types";
import { CommentPanel } from "./CommentPanel";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { formatScore, ScoreBar } from "./ScoreBar";

interface ModelResponseCardProps {
  response: DisplayModelResponse;
  elapsedSeconds: number;
  feedbackSubmitting: boolean;
  showComments?: boolean;
  onFeedback: (responseId: number, feedbackType: FeedbackToggleResult["feedbackType"]) => void;
}

const dimensionLabels: Array<{ key: keyof EvaluationScore; label: string; weight: string }> = [
  { key: "relevance", label: "相关性", weight: "30%" },
  { key: "completeness", label: "完整性", weight: "25%" },
  { key: "clarity", label: "清晰度", weight: "20%" },
  { key: "format", label: "格式", weight: "15%" },
  { key: "safety", label: "安全性", weight: "10%" }
];

export function ModelResponseCard({
  response,
  elapsedSeconds,
  feedbackSubmitting,
  showComments = false,
  onFeedback
}: ModelResponseCardProps) {
  const [detailVisible, setDetailVisible] = useState(false);
  const detailRef = useRef<HTMLElement | null>(null);

  if (isPendingResponse(response)) {
    return (
      <article className="response-card pending">
        <ResponseHeader modelName={response.modelName} statusLabel="等待模型响应" scoreText="..." failed={false} />
        <div className="pending-answer" aria-label="模型响应等待中">
          <span />
          <span />
          <span />
        </div>
        <dl className="metric-row">
          <Metric label="耗时" value={`${elapsedSeconds}s`} />
          <Metric label="输出" value="等待中" />
          <Metric label="成本" value="待估算" />
        </dl>
      </article>
    );
  }

  if ("streaming" in response) {
    return (
      <article className={`response-card${response.scoring ? " scoring" : ""}`}>
        <ResponseHeader
          modelName={response.modelName}
          statusLabel={response.scoring ? "评分中……" : "生成中"}
          scoreText={response.scoring ? "评分中" : "..."}
          failed={false}
        />
        <ScrollableMarkdownAnswer content={response.answer} placeholder="模型回答已生成，正在准备评分。" />
        <dl className="metric-row">
          <Metric label="耗时" value={`${elapsedSeconds}s`} />
          <Metric label="输出" value={response.scoring ? "等待评分" : "生成中"} />
          <Metric label="成本" value="待估算" />
        </dl>
      </article>
    );
  }

  const score = normalizedScore(response.score);
  const feedback = response.feedback;
  const failed = response.status !== "success";

  return (
    <article className={`response-card${failed ? " failed" : ""}`}>
      <ResponseHeader
        modelName={response.modelName}
        statusLabel={failed ? "调用失败" : "调用成功"}
        scoreText={failed ? "失败" : formatScore(score.final)}
        failed={failed}
      />
      <ScrollableMarkdownAnswer content={response.answer} placeholder="暂无回答内容" />
      <dl className="metric-row">
        <Metric label="耗时" value={`${response.latencyMs}ms`} />
        <Metric label="输出" value={String(response.outputTokens)} />
        <Metric label="成本" value={`${formatCost(response.estimatedCost)} ${response.currency}`} />
      </dl>
      <div className="score-bars">
        <ScoreBar label="相关性" value={score.relevance} />
        <ScoreBar label="完整性" value={score.completeness} />
        <ScoreBar label="清晰度" value={score.clarity} />
      </div>
      <footer className="card-actions">
        <Button
          className={feedback.liked ? "active" : ""}
          disabled={feedbackSubmitting}
          onClick={() => onFeedback(response.id, "like")}
        >
          点赞 {feedback.likeCount}
        </Button>
        <Button
          danger
          className={feedback.disliked ? "danger active" : "danger"}
          disabled={feedbackSubmitting}
          onClick={() => onFeedback(response.id, "dislike")}
        >
          点踩 {feedback.dislikeCount}
        </Button>
        <Button type="primary" ghost onClick={() => setDetailVisible(true)}>
          查看全文
        </Button>
      </footer>
      <Modal
        title={`${response.modelName} · 回答详情`}
        open={detailVisible}
        width="min(860px, 94vw)"
        footer={null}
        onCancel={() => setDetailVisible(false)}
        afterOpenChange={(open) => {
          if (open) {
            animateModalIn(detailRef.current);
          }
        }}
      >
        <section ref={detailRef} className="response-detail-modal">
          <MarkdownRenderer content={response.answer} />
          <div className="score-detail-list">
            {dimensionLabels.map((dimension) => {
              const value = score[dimension.key];
              const details = score.details[dimension.key] || ["暂无命中项明细"];
              return (
                <article key={dimension.key} className="score-detail-item">
                  <header>
                    <span>{dimension.label}</span>
                    <Space size={8}>
                      <strong>{typeof value === "number" ? `${formatScore(value)} / 10` : "-"}</strong>
                      <em>权重 {dimension.weight}</em>
                    </Space>
                  </header>
                  <ul>
                    {details.map((detail) => (
                      <li key={detail}>{detail}</li>
                    ))}
                  </ul>
                </article>
              );
            })}
          </div>
          <article className="score-detail-item">
            <header>
              <span>用户反馈</span>
              <Space size={8}>
                <strong>{feedback.liked ? "已点赞" : feedback.disliked ? "已点踩" : "未反馈"}</strong>
                <em>权重 10%</em>
              </Space>
            </header>
            <p>
              点赞 {feedback.likeCount} 次，点踩 {feedback.dislikeCount} 次。
              {score.feedbackScore === null || score.feedbackScore === undefined
                ? "暂无点赞或点踩，最终分保持基础分不变。"
                : `最终分 = 基础分 ${formatScore(score.baseFinal)} x 90% + 反馈分 ${formatScore(score.feedbackScore)} x 10%。`}
            </p>
          </article>
          {score.judgeComment ? (
            <article className="score-detail-item">
              <header>
                <span>LLM 评审理由</span>
                <Space size={8}>
                  <strong>{formatScore(score.judgeFinal)} / 10</strong>
                  <em>权重 40%</em>
                </Space>
              </header>
              <p>{score.judgeComment}</p>
            </article>
          ) : null}
          {showComments ? <CommentPanel responseId={response.id} /> : null}
        </section>
      </Modal>
    </article>
  );
}

interface ScrollMetrics {
  scrollTop: number;
  clientHeight: number;
  scrollHeight: number;
}

export function isNearScrollBottom(metrics: ScrollMetrics, threshold = 28): boolean {
  return metrics.scrollHeight - metrics.scrollTop - metrics.clientHeight <= threshold;
}

function ScrollableMarkdownAnswer({
  content,
  placeholder
}: {
  content: string;
  placeholder: string;
}) {
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const shouldStickToBottomRef = useRef(true);
  const displayContent = content || placeholder;

  useLayoutEffect(() => {
    const element = scrollRef.current;
    if (!element || !shouldStickToBottomRef.current) {
      return;
    }
    element.scrollTop = element.scrollHeight;
  }, [displayContent]);

  function handleScroll(): void {
    const element = scrollRef.current;
    if (!element) {
      return;
    }
    shouldStickToBottomRef.current = isNearScrollBottom(element);
  }

  return (
    <div ref={scrollRef} className="answer-scroll" onScroll={handleScroll}>
      <MarkdownRenderer content={displayContent} />
    </div>
  );
}

function ResponseHeader({
  modelName,
  statusLabel,
  scoreText,
  failed
}: {
  modelName: string;
  statusLabel: string;
  scoreText: string;
  failed: boolean;
}) {
  return (
    <header className="response-head">
      <div>
        <p className="panel-label">模型名称</p>
        <h3>{modelName}</h3>
      </div>
      <div className="response-status">
        <span className={failed ? "status-badge failed" : "status-badge"}>{statusLabel}</span>
        <strong className={failed ? "failed" : ""}>{scoreText}</strong>
      </div>
    </header>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function normalizedScore(score: EvaluationScore): Required<EvaluationScore> {
  return {
    relevance: score.relevance || 0,
    completeness: score.completeness || 0,
    clarity: score.clarity || 0,
    format: score.format || 0,
    safety: score.safety || 0,
    final: score.final || 0,
    details: score.details || {},
    ruleFinal: score.ruleFinal ?? score.final ?? 0,
    judgeFinal: score.judgeFinal ?? null,
    baseFinal: score.baseFinal ?? score.final ?? 0,
    feedbackScore: score.feedbackScore ?? null,
    judgeComment: score.judgeComment ?? null,
    judgeDetails: score.judgeDetails || {}
  };
}

function formatCost(value: number): string {
  return value.toFixed(4).replace(/0+$/, "").replace(/\.$/, ".0");
}
