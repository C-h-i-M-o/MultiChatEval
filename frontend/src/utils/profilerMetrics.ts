// React Profiler 采样辅助代码。
// 本次采样结果已经记录到 docs/performance-metrics-report.md。
// 如需重新采样，取消本文件注释，并按 EvaluationPage.tsx 和 ModelResponseCard.tsx 中的注释包裹组件。
//
// import type { ProfilerOnRenderCallback } from "react";
//
// export interface ProfilerMetric {
//   id: string;
//   phase: "mount" | "update" | "nested-update";
//   actualDuration: number;
//   baseDuration: number;
//   startTime: number;
//   commitTime: number;
// }
//
// declare global {
//   interface Window {
//     __MCE_PROFILER_METRICS__?: ProfilerMetric[];
//   }
// }
//
// export const recordProfilerRender: ProfilerOnRenderCallback = (
//   id,
//   phase,
//   actualDuration,
//   baseDuration,
//   startTime,
//   commitTime
// ) => {
//   const metrics = window.__MCE_PROFILER_METRICS__ ?? [];
//   metrics.push({
//     id,
//     phase,
//     actualDuration,
//     baseDuration,
//     startTime,
//     commitTime
//   });
//   window.__MCE_PROFILER_METRICS__ = metrics;
// };
