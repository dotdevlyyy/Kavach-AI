"use client";

import { cx } from "@/components/boardui/utils/cx";
import { useEffect, useState } from "react";

export type LoadingVariant = "drive" | "dots" | "orbit";

export function LoadingState({
  variant = "drive",
  label = "Working",
  startTime,
  className,
}: {
  variant?: LoadingVariant;
  label?: string;
  startTime?: number | Date;
  className?: string;
}) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    if (startTime === undefined) return;
    const started = startTime instanceof Date ? startTime.getTime() : startTime;
    const update = () => setElapsed(Math.max(0, (Date.now() - started) / 1000));
    update();
    const timer = window.setInterval(update, 250);
    return () => window.clearInterval(timer);
  }, [startTime]);
  const order = variant === "orbit" ? [0, 1, 2, 5, 8, 7, 6, 3] : Array.from({ length: 9 }, (_, index) => index);
  return (
    <div role="status" className={cx("w-fit", className)}>
      <style>{`@keyframes kavach-pixel{0%,55%,100%{opacity:.15;transform:scale(.86)}25%{opacity:1;transform:scale(1)}}@media(prefers-reduced-motion:reduce){[data-kavach-pixel]{animation:none!important}}`}</style>
      <div className="flex min-h-7 items-center gap-2.5">
        <span aria-hidden className="grid shrink-0 grid-cols-[repeat(3,4px)] gap-[1.5px]">
          {Array.from({ length: 9 }, (_, index) => {
            const delay = order.indexOf(index);
            return <span key={index} data-kavach-pixel className={cx("size-1 bg-foreground", variant === "dots" ? "rounded-full" : "rounded-[1px]")} style={{ animation: `${variant === "orbit" ? 950 : 650}ms ease-in-out ${delay < 0 ? 0 : delay * 110}ms infinite kavach-pixel` }} />;
          })}
        </span>
        <span className="text-sm font-medium text-foreground">{label}</span>
        {startTime !== undefined && <span suppressHydrationWarning className="font-mono text-xs tabular-nums text-muted-foreground">{elapsed < 60 ? `${elapsed.toFixed(elapsed < 10 ? 1 : 0)}s` : `${Math.floor(elapsed / 60)}m ${Math.floor(elapsed % 60)}s`}</span>}
      </div>
    </div>
  );
}
