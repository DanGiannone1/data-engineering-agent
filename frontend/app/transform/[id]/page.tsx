"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  getStatus,
  getMessages,
  submitReview,
  Message,
  TransformStatus,
} from "@/lib/api";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import ApprovalControls from "@/components/ApprovalControls";
import StatusBadge from "@/components/StatusBadge";

const POLL_INTERVAL = 3000;

export default function TransformChat() {
  const params = useParams();
  const router = useRouter();
  const instanceId = params.id as string;

  const [messages, setMessages] = useState<Message[]>([]);
  const [status, setStatus] = useState<TransformStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const isRunning = status?.runtime_status === "Running";
  const isWaiting =
    isRunning &&
    messages.length > 0 &&
    messages[messages.length - 1]?.role === "agent";

  // Determine current phase from latest message
  const latestPhase = messages.length > 0
    ? messages[messages.length - 1].phase
    : null;
  const isPendingReview =
    isWaiting &&
    (latestPhase === "pseudocode_review" || latestPhase === "output_review");

  useEffect(() => {
    const interval = setInterval(async () => {
      try {
        const [s, m] = await Promise.all([
          getStatus(instanceId),
          getMessages(instanceId),
        ]);
        setStatus(s);
        setMessages(m);
      } catch {
        // ignore polling errors
      }
    }, POLL_INTERVAL);

    // Initial fetch
    Promise.all([getStatus(instanceId), getMessages(instanceId)]).then(
      ([s, m]) => {
        setStatus(s);
        setMessages(m);
      }
    );

    return () => clearInterval(interval);
  }, [instanceId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function handleApprove() {
    setLoading(true);
    try {
      await submitReview(instanceId, { approved: true });
    } finally {
      setLoading(false);
    }
  }

  async function handleReject(feedback: string) {
    setLoading(true);
    try {
      await submitReview(instanceId, { approved: false, feedback });
    } finally {
      setLoading(false);
    }
  }

  async function handleSend(text: string) {
    setLoading(true);
    try {
      await submitReview(instanceId, { approved: false, feedback: text });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-8 flex flex-col h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => router.push("/")}
            className="text-gray-500 hover:text-gray-700"
          >
            &larr; Back
          </button>
          <h1 className="text-xl font-bold text-gray-900">
            Transformation
          </h1>
        </div>
        <StatusBadge
          runtimeStatus={status?.runtime_status ?? null}
          phase={latestPhase ?? undefined}
        />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-gray-100 rounded-lg p-4 mb-4">
        {messages.length === 0 && (
          <p className="text-gray-500 text-center py-8">
            Waiting for agent to start processing...
          </p>
        )}
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Controls */}
      {isPendingReview ? (
        <ApprovalControls
          onApprove={handleApprove}
          onReject={handleReject}
          disabled={loading}
        />
      ) : isRunning ? (
        <ChatInput onSend={handleSend} disabled={!isWaiting || loading} />
      ) : status?.runtime_status === "Completed" ? (
        <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-center text-green-800">
          Transformation completed successfully.
        </div>
      ) : status?.runtime_status === "Failed" ? (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-center text-red-800">
          Transformation failed. Check the messages above for details.
        </div>
      ) : null}
    </div>
  );
}
