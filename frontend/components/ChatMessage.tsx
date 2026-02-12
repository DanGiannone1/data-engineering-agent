import type { Message } from "@/lib/api";

interface Props {
  message: Message;
}

export default function ChatMessage({ message }: Props) {
  const isAgent = message.role === "agent";

  // For structured pseudocode messages, show a summary instead of raw JSON
  const displayContent = (() => {
    if (message.structured_pseudocode) {
      const pc = message.structured_pseudocode;
      return `${pc.summary}\n\n(${pc.steps?.length || 0} transformation steps - see review panel below)`;
    }
    return message.content;
  })();

  return (
    <div className={`flex ${isAgent ? "justify-start" : "justify-end"} mb-4`}>
      <div
        className={`max-w-[80%] rounded-lg px-4 py-3 ${
          isAgent
            ? "bg-white border border-gray-200 text-gray-900"
            : "bg-blue-600 text-white"
        }`}
      >
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs font-medium opacity-70">
            {isAgent ? "Agent" : "You"}
          </span>
          <span className="text-xs opacity-50">
            {new Date(message.timestamp).toLocaleTimeString()}
          </span>
        </div>
        <div className="whitespace-pre-wrap text-sm">{displayContent}</div>
      </div>
    </div>
  );
}
