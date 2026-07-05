import type { RefObject } from "react";
import gsap from "gsap";
import { useGSAP } from "@gsap/react";

gsap.registerPlugin(useGSAP);

type MotionScope = RefObject<HTMLElement | null>;

function shouldReduceMotion(): boolean {
  return window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
}

export function useWorkspaceMotion(scope: MotionScope, routeKey: string): void {
  useGSAP(
    () => {
      if (!scope.current) {
        return;
      }

      const select = gsap.utils.selector(scope.current);
      const heading = select(".page-head");
      const surfaces = select(
        ".notice-panel, .token-usage-panel, .query-panel, .waiting-banner, .response-card, .history-panel, .history-detail, .comment-panel, .admin-tab-panel-stack, .user-filter-bar, .admin-table-panel, .feedback-section, .ant-card"
      ).filter((element) => !element.closest(".admin-tab-panel-stack") || element.classList.contains("admin-tab-panel-stack"));

      if (shouldReduceMotion()) {
        gsap.set([...heading, ...surfaces], { autoAlpha: 1, clearProps: "transform,filter" });
        return;
      }

      // 路由切换时统一处理主页面入场，避免每个业务页重复写动画。
      const timeline = gsap.timeline({ defaults: { ease: "power3.out" } });
      timeline
        .from(heading, { autoAlpha: 0, y: 24, filter: "blur(8px)", duration: 0.48 })
        .from(
          surfaces,
          {
            autoAlpha: 0,
            y: 28,
            scale: 0.985,
            filter: "blur(10px)",
            duration: 0.48,
            stagger: 0.045,
            clearProps: "transform,filter,opacity,visibility"
          },
          "-=0.24"
        );
    },
    { scope, dependencies: [routeKey], revertOnUpdate: true }
  );
}

export function useAuthMotion(scope: MotionScope): void {
  useGSAP(
    () => {
      if (!scope.current) {
        return;
      }

      if (shouldReduceMotion()) {
        gsap.set(scope.current, { autoAlpha: 1, clearProps: "transform,filter" });
        return;
      }

      // 登录页只做一次品牌卡片入场，突出 logo 但不影响表单可用性。
      const select = gsap.utils.selector(scope.current);
      const timeline = gsap.timeline({ defaults: { ease: "back.out(1.25)" } });
      timeline
        .from(scope.current, { autoAlpha: 0, y: 30, scale: 0.96, filter: "blur(12px)", duration: 0.58 })
        .from(select(".brand-logo"), { rotate: -8, scale: 0.72, duration: 0.46 }, "-=0.28")
        .from(select(".auth-form label, .auth-submit, .auth-switch"), { autoAlpha: 0, y: 12, stagger: 0.06 }, "-=0.2");
    },
    { scope }
  );
}

export function useResponseGridMotion(scope: MotionScope, responseCount: number): void {
  useGSAP(
    () => {
      if (!scope.current || responseCount === 0 || shouldReduceMotion()) {
        return;
      }

      // 模型结果是渐进返回的，只动画最新进入视野的一组卡片。
      const cards = gsap.utils.toArray<HTMLElement>(".response-card", scope.current);
      gsap.fromTo(
        cards.slice(Math.max(0, cards.length - responseCount)),
        { autoAlpha: 0, rotateX: -8, y: 22, transformOrigin: "50% 0%" },
        { autoAlpha: 1, rotateX: 0, y: 0, duration: 0.38, stagger: 0.04, ease: "power3.out" }
      );
    },
    { scope, dependencies: [responseCount], revertOnUpdate: false }
  );
}

export function animateModalIn(element: HTMLElement | null): void {
  if (!element || shouldReduceMotion()) {
    return;
  }

  // AntD 弹窗打开后再轻微放大进入，避免与组件自身动画冲突。
  gsap.fromTo(
    element,
    { autoAlpha: 0, y: 18, scale: 0.965, filter: "blur(8px)" },
    { autoAlpha: 1, y: 0, scale: 1, filter: "blur(0px)", duration: 0.34, ease: "power3.out" }
  );
}
