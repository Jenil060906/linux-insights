import type { ReactNode } from "react";
import { motion } from "framer-motion";

interface FadeInProps {
  children: ReactNode;
  delay?: number;
  className?: string;
}

// Subtle mount-in transition for dashboard sections. Respects prefers-reduced-motion
// via the MotionConfig set at the app root.
export function FadeIn({ children, delay = 0, className }: FadeInProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, delay, ease: "easeOut" }}
      className={className}
    >
      {children}
    </motion.div>
  );
}
