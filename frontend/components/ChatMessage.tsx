import type { Message } from "@/lib/api";

interface Props {
  message: Message;
}

function renderMarkdown(text: string): React.ReactNode[] {
  const lines = text.split("\n");
  const result: React.ReactNode[] = [];
  let listItems: string[] = [];

  function flushList() {
    if (listItems.length > 0) {
      result.push(
        <ul key={`ul-${result.length}`} className="list-disc list-inside my-1 space-y-0.5">
          {listItems.map((item, i) => (
            <li key={i}>{applyInline(item)}</li>
          ))}
        </ul>
      );
      listItems = [];
    }
  }

  function applyInline(s: string): React.ReactNode {
    // Convert **bold** to <strong>
    const parts = s.split(/(\*\*[^*]+\*\*)/g);
    if (parts.length === 1) return s;
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Heading: #### text → bold block
    const headingMatch = line.match(/^#{1,6}\s+(.+)$/);
    if (headingMatch) {
      flushList();
      result.push(
        <p key={`h-${i}`} className="font-semibold mt-2 mb-1">
          {applyInline(headingMatch[1])}
        </p>
      );
      continue;
    }

    // Bullet: - text or * text
    const bulletMatch = line.match(/^\s*[-*]\s+(.+)$/);
    if (bulletMatch) {
      listItems.push(bulletMatch[1]);
      continue;
    }

    // Empty line
    if (line.trim() === "") {
      flushList();
      result.push(<br key={`br-${i}`} />);
      continue;
    }

    // Regular text
    flushList();
    result.push(
      <p key={`p-${i}`} className="my-0.5">
        {applyInline(line)}
      </p>
    );
  }

  flushList();
  return result;
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

  // Use markdown rendering for agent messages (may contain headers, bold, bullets)
  const renderedContent = isAgent
    ? renderMarkdown(displayContent)
    : displayContent;

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
        <div className="text-sm">
          {isAgent ? renderedContent : <span className="whitespace-pre-wrap">{renderedContent}</span>}
        </div>
      </div>
    </div>
  );
}
