import { useEffect, useRef, useState } from "react";

function easeOutCubic(t: number): number {
  return 1 - (1 - t) ** 3;
}

// Tweens a fixed-length number array toward `target` over `durationMs` instead
// of snapping straight to it — used to animate sparklines (or any small numeric
// series) smoothly on every live-data tick, without depending on SVG-attribute
// animation support in a charting library.
export function useAnimatedSeries(target: number[], durationMs = 500): number[] {
  const [displayed, setDisplayed] = useState<number[]>(target);
  const fromRef = useRef<number[]>(target);
  const rafRef = useRef(0);

  useEffect(() => {
    if (fromRef.current.length !== target.length) {
      fromRef.current = target;
      setDisplayed(target);
      return;
    }

    const from = fromRef.current;
    const start = performance.now();
    cancelAnimationFrame(rafRef.current);

    const step = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs);
      const eased = easeOutCubic(t);
      const next = from.map((v, i) => v + (target[i] - v) * eased);
      setDisplayed(next);
      if (t < 1) {
        rafRef.current = requestAnimationFrame(step);
      } else {
        fromRef.current = target;
      }
    };

    rafRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, durationMs]);

  return displayed;
}
