"use client";

import { useState } from "react";
import { Message } from "@/lib/api";

interface Props {
  messages: Message[];
}

interface VersionEntry {
  version: number;
  timestamp: string;
  isInitial: boolean;
  feedbackBefore?: string;
}

export default function VersionHistory({ messages }: Props) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Extract version history from messages
  const versions: VersionEntry[] = [];
  let versionCount = 0;

  for (let i = 0; i < messages.length; i++) {
    const msg = messages[i];
    if (
      msg.phase === "pseudocode_review" &&
      msg.role === "agent" &&
      msg.structured_pseudocode
    ) {
      versionCount++;
      const prevMsg = i > 0 ? messages[i - 1] : null;
      const feedbackBefore =
        prevMsg?.role === "auditor" && prevMsg?.phase === "pseudocode_review"
          ? prevMsg.content
          : undefined;

      versions.push({
        version: msg.structured_pseudocode.version || versionCount,
        timestamp: msg.timestamp,
        isInitial: versionCount === 1,
        feedbackBefore,
      });
    }
  }

  if (versions.length <= 1) {
    return null;
  }

  const currentVersion = versions[versions.length - 1];
  const previousVersions = versions.slice(0, -1).reverse();

  return (
    <div className="mb-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
      >
        <svg
          className={`w-4 h-4 transition-transform ${
            isExpanded ? "rotate-90" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5l7 7-7 7"
          />
        </svg>
        Version History ({versions.length} versions)
      </button>

      {isExpanded && (
        <div className="mt-3 border border-gray-200 rounded-lg overflow-hidden">
          {/* Current version */}
          <div className="px-4 py-3 bg-blue-50 border-b border-gray-200">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-blue-700">
                v{currentVersion.version} (current)
              </span>
              <span className="text-xs text-gray-500">
                {new Date(currentVersion.timestamp).toLocaleTimeString()}
              </span>
            </div>
            {currentVersion.feedbackBefore && (
              <p className="text-xs text-gray-600 mt-1">
                Changes based on: &quot;{currentVersion.feedbackBefore.slice(0, 100)}
                {currentVersion.feedbackBefore.length > 100 ? "..." : ""}&quot;
              </p>
            )}
          </div>

          {/* Previous versions */}
          {previousVersions.map((v) => (
            <div
              key={v.version}
              className="px-4 py-2 border-b last:border-0 border-gray-100"
            >
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-600">
                  v{v.version}
                  {v.isInitial && (
                    <span className="text-gray-400 ml-1">(initial)</span>
                  )}
                </span>
                <span className="text-xs text-gray-400">
                  {new Date(v.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
