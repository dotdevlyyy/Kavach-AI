import { Cpu, Eye, Code } from "lucide-react";

type ModelType = "llama3.2:1b" | "qwen2.5-coder:1.5b" | "qwen2.5vl:3b";

interface ModelBadgeProps {
  model: ModelType;
}

export function ModelBadge({ model }: ModelBadgeProps) {
  let icon = <Cpu className="w-3 h-3 mr-1" />;
  let label = "Llama 3.2 (1B)";
  let bgClass = "bg-primary/10 text-primary border-primary/20";

  if (model === "qwen2.5-coder:1.5b") {
    icon = <Code className="w-3 h-3 mr-1" />;
    label = "Qwen Coder (1.5B)";
    bgClass = "bg-secondary/10 text-secondary border-secondary/20";
  } else if (model === "qwen2.5vl:3b") {
    icon = <Eye className="w-3 h-3 mr-1" />;
    label = "Qwen Vision (3B)";
    bgClass = "bg-purple-500/10 text-purple-400 border-purple-500/20";
  }

  return (
    <div className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium border ${bgClass}`}>
      {icon}
      {label}
    </div>
  );
}
