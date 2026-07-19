import type { ReactNode } from "react";
import type { LucideIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { SectionHeader } from "@/components/common/SectionHeader";

interface SectionCardProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
}

// Standard Card + SectionHeader + CardContent shell shared by every dashboard section.
// Extracted so each section only owns its content, not the surrounding chrome.
export function SectionCard({
  title,
  description,
  icon,
  action,
  children,
  className,
  contentClassName,
}: SectionCardProps) {
  return (
    <Card className={className}>
      <div className="p-4 pb-0">
        <SectionHeader title={title} description={description} icon={icon} action={action} />
      </div>
      <CardContent className={contentClassName}>{children}</CardContent>
    </Card>
  );
}
